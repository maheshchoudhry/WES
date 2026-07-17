"""Phase 1 (WP6) — Founder Project Intake + Autonomous Decomposition.

Proves: a Founder intake objective is analysed by the AI CEO and automatically
decomposed into epics -> sprints -> tasks with REAL AI-employee assignment, in a
plan-awaiting-approval state that does NOT begin implementation. Backward
compatibility of the existing project API is also asserted.
"""


def _create_intake(client):
    return client.post(
        "/api/v1/projects",
        json={
            "code": "PROJ-INTAKE-1",
            "name": "Inventory Module",
            "business_objective": "Give the studio a real-time inventory module",
            "business_problem": "No visibility into stock levels",
            "deliverables": ["Inventory API", "Inventory Dashboard", "Stock Alerts"],
            "constraints": ["Must reuse the existing auth", "No new database engine"],
            "acceptance_criteria": "Founder can view live stock and receive alerts",
            "priority": "high",
            "timeline": "2 sprints",
        },
    )


def test_intake_project_creates_with_objective(client, ai_seeded):
    resp = _create_intake(client)
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["business_objective"].startswith("Give the studio")
    assert data["plan_status"] is None  # not decomposed yet


def test_backward_compatible_minimal_project(client, ai_seeded):
    # The pre-existing minimal create (code + name only) must still work.
    resp = client.post("/api/v1/projects", json={"code": "PLAIN-1", "name": "Plain Project"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["plan_status"] is None


def test_decomposition_produces_epics_sprints_tasks_with_assignees(client, ai_seeded):
    pid = _create_intake(client).json()["data"]["id"]
    plan = client.post(f"/api/v1/projects/{pid}/decompose").json()["data"]

    # Business analysis performed by the AI CEO.
    assert plan["business_analysis"]["analyst"]
    assert plan["business_analysis"]["vision"]
    assert plan["business_analysis"]["risks"]

    # One epic per deliverable, one sprint per epic, tasks under each.
    assert plan["totals"]["epics"] == 3
    assert plan["totals"]["sprints"] == 3
    assert plan["totals"]["tasks"] == 3 * 5  # 5-task lifecycle template per epic
    assert plan["totals"]["estimated_hours"] > 0

    # Every task is assigned to a REAL AI employee (not a label).
    assert all(t["assignee"] for t in plan["tasks"])
    roles_used = {t["assignee"] for t in plan["tasks"]}
    assert len(roles_used) >= 3  # architect / backend / frontend / qa / writer

    # Plan awaits approval; implementation has NOT begun.
    assert plan["project"]["plan_status"] == "decomposed"
    assert plan["project"]["status"] == "planning"


def test_decomposition_does_not_start_implementation(client, ai_seeded):
    pid = _create_intake(client).json()["data"]["id"]
    client.post(f"/api/v1/projects/{pid}/decompose")
    # No development task/run was triggered by decomposition.
    dev = client.get("/api/v1/development/tasks").json()["data"]
    assert dev == [] or all(t.get("status") == "queued" for t in dev)
    # Tasks are in backlog, not in progress.
    plan = client.get(f"/api/v1/projects/{pid}/plan").json()["data"]
    assert all(t["status"] == "backlog" for t in plan["tasks"])


def test_founder_approves_plan(client, ai_seeded):
    pid = _create_intake(client).json()["data"]["id"]
    client.post(f"/api/v1/projects/{pid}/decompose")
    approved = client.post(f"/api/v1/projects/{pid}/approve-plan").json()["data"]
    assert approved["project"]["plan_status"] == "approved"


def test_decompose_is_idempotent(client, ai_seeded):
    pid = _create_intake(client).json()["data"]["id"]
    first = client.post(f"/api/v1/projects/{pid}/decompose").json()["data"]
    second = client.post(f"/api/v1/projects/{pid}/decompose").json()["data"]
    # Re-running replaces the prior plan rather than duplicating it.
    assert first["totals"]["tasks"] == second["totals"]["tasks"] == 15
