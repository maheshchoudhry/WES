"""Phase 2 (WP3) — durable execution via the API + development workflow handler."""

from app.services.job_worker import run_once


def test_run_async_enqueues_and_worker_completes(client, quality_seeded, SessionFactory):
    # Create a development task (new-module scaffold path — deterministic).
    task = client.post(
        "/api/v1/development/tasks", json={"title": "Add a slug helper utility"}
    ).json()["data"]

    # Enqueue it as a DURABLE background job (does not run synchronously).
    job = client.post(
        f"/api/v1/development/tasks/{task['id']}/run-async", json={}
    ).json()["data"]
    assert job["status"] == "queued"
    assert job["job_type"] == "development_workflow"

    # The task has not run yet.
    assert client.get(f"/api/v1/development/tasks/{task['id']}").json()["data"]["status"] == "queued"

    # The worker claims and runs it durably.
    assert run_once(SessionFactory) is True

    # Job completed; the development task reached a terminal workflow state.
    done = client.get(f"/api/v1/jobs/{job['id']}").json()["data"]
    assert done["status"] == "completed"
    assert done["progress_pct"] == 100
    assert done["result"]["status"] in ("pr_ready", "changes_requested", "failed")

    t = client.get(f"/api/v1/development/tasks/{task['id']}").json()["data"]
    assert t["status"] in ("pr_ready", "changes_requested")


def test_jobs_list_and_idempotent_async_enqueue(client, quality_seeded, SessionFactory):
    task = client.post(
        "/api/v1/development/tasks", json={"title": "Add a cache helper"}
    ).json()["data"]
    j1 = client.post(f"/api/v1/development/tasks/{task['id']}/run-async", json={}).json()["data"]
    j2 = client.post(f"/api/v1/development/tasks/{task['id']}/run-async", json={}).json()["data"]
    # Idempotent: same task → same job (no duplicate queue entry).
    assert j1["id"] == j2["id"]

    listing = client.get("/api/v1/jobs").json()["data"]
    assert any(j["id"] == j1["id"] for j in listing)

    # Cancel it while queued.
    cancelled = client.post(f"/api/v1/jobs/{j1['id']}/cancel").json()["data"]
    assert cancelled["status"] == "cancelled"
    assert run_once(SessionFactory) is False  # nothing runnable
