"""Phase 4 — autonomous lifecycle chain.

Founder approves once at the plan and once at the PR; everything between runs
automatically on the durable queue: plan approval → task execution → PR (approval)
→ pipeline → staging deploy → monitoring → Founder notification.
"""

from app.services.job_worker import run_once


def _project(client):
    return client.post(
        "/api/v1/projects",
        json={
            "code": "CHAIN-1",
            "name": "Chain Module",
            "business_objective": "Prove the autonomous chain",
            "deliverables": ["Widget API"],  # 1 epic → 5 tasks
        },
    ).json()["data"]


def test_plan_approval_enqueues_project_execution(client, quality_seeded):
    pid = _project(client)["id"]
    client.post(f"/api/v1/projects/{pid}/decompose")
    client.post(f"/api/v1/projects/{pid}/approve-plan")
    jobs = client.get("/api/v1/jobs").json()["data"]
    assert any(j["job_type"] == "project_execution" and j["status"] == "queued" for j in jobs)


def test_project_execution_creates_and_runs_tasks(client, quality_seeded, SessionFactory):
    pid = _project(client)["id"]
    client.post(f"/api/v1/projects/{pid}/decompose")
    client.post(f"/api/v1/projects/{pid}/approve-plan")

    # Run the project-execution job → dev tasks + dev-workflow jobs are created.
    assert run_once(SessionFactory) is True
    dev = client.get("/api/v1/development/tasks").json()["data"]
    assert len(dev) == 5  # one per work item
    jobs = client.get("/api/v1/jobs").json()["data"]
    assert sum(1 for j in jobs if j["job_type"] == "development_workflow") == 5

    # A Founder notification announced autonomous execution.
    notes = client.get("/api/v1/notifications").json()["data"]
    assert any(n["kind"] == "project_execution" for n in notes)

    # Run one development workflow → it completes and (if pr_ready) notifies.
    assert run_once(SessionFactory) is True
    completed = [
        t
        for t in client.get("/api/v1/development/tasks").json()["data"]
        if t["status"] in ("pr_ready", "changes_requested")
    ]
    assert len(completed) >= 1


def test_pr_approval_auto_starts_pipeline_and_notifies(client, quality_seeded, SessionFactory):
    # A completed, gate-eligible dev task.
    task = client.post(
        "/api/v1/development/run", json={"title": "Add a slug helper utility"}
    ).json()["data"]
    assert task["status"] == "pr_ready"

    # Founder approves the PR → pipeline job auto-enqueued.
    client.post(
        f"/api/v1/development/tasks/{task['id']}/approve", json={"decision": "approved"}
    )
    jobs = client.get("/api/v1/jobs").json()["data"]
    assert any(j["job_type"] == "devops_pipeline" and j["status"] == "queued" for j in jobs)

    # Worker runs the pipeline (build → test → scan → staging deploy → monitor).
    assert run_once(SessionFactory) is True
    pipe_job = next(
        j
        for j in client.get("/api/v1/jobs").json()["data"]
        if j["job_type"] == "devops_pipeline"
    )
    assert pipe_job["status"] == "completed"

    # Founder receives a deployment-complete notification.
    notes = client.get("/api/v1/notifications").json()["data"]
    assert any(n["kind"] == "deployment" for n in notes)


def test_notifications_api(client, quality_seeded):
    task = client.post(
        "/api/v1/development/run", json={"title": "Add a cache helper"}
    ).json()["data"]
    client.post(f"/api/v1/development/tasks/{task['id']}/approve", json={"decision": "approved"})
    # (approval created no notification by itself, but the endpoints must work)
    from app.services.notifications import NotificationService  # noqa

    before = client.get("/api/v1/notifications/unread-count").json()["data"]["unread"]
    assert isinstance(before, int)
    resp = client.post("/api/v1/notifications/read-all")
    assert resp.status_code == 200
    assert client.get("/api/v1/notifications/unread-count").json()["data"]["unread"] == 0
