"""Phase 3 (WP7) — Real AI-employee orchestration.

Proves the development workflow is performed by ACTUAL employees (not role labels):
a real employee (+ selected provider) is recorded for every stage, and handoffs
between employees are recorded.
"""


def test_team_lists_acting_employees_with_policy(client, quality_seeded):
    team = client.get("/api/v1/development/team").json()["data"]
    assert len(team) >= 5
    by_role = {a["role"].lower(): a for a in team}
    # Real employees with authority, a selected provider, and decision rules.
    assert all(a["employee"] for a in team)
    assert all(a["provider"] for a in team)
    assert any("engineer" in r for r in by_role)
    backend = next(a for a in team if "backend" in a["role"].lower())
    assert backend["decision_rules"]  # non-empty policy
    assert backend["provider"]  # provider selected for this employee


def test_workflow_records_real_employees_per_stage(client, quality_seeded):
    task = client.post(
        "/api/v1/development/run", json={"title": "Add a slug helper utility"}
    ).json()["data"]
    orch = client.get(f"/api/v1/development/tasks/{task['id']}/orchestration").json()["data"]

    stages = orch["stages"]
    # Every executed stage was performed by a REAL named employee (not just a label).
    acting = [s for s in stages if s["acting_employee"]]
    assert len(acting) >= 5
    assert all(s["provider"] for s in acting)
    employees = {s["acting_employee"] for s in acting}
    assert len(employees) >= 3  # multiple distinct employees collaborated


def test_handoffs_are_recorded_between_employees(client, quality_seeded):
    task = client.post(
        "/api/v1/development/run", json={"title": "Add a cache helper"}
    ).json()["data"]
    orch = client.get(f"/api/v1/development/tasks/{task['id']}/orchestration").json()["data"]

    handoffs = orch["handoffs"]
    assert len(handoffs) >= 1
    for h in handoffs:
        # A handoff is between two DIFFERENT real employees.
        assert h["from_employee"] and h["to_employee"]
        assert h["from_employee"] != h["to_employee"]
        assert h["summary"]


def test_timeline_backward_compatible(client, quality_seeded):
    # The existing timeline still works and now carries acting employee + provider.
    task = client.post(
        "/api/v1/development/run", json={"title": "Add a config loader"}
    ).json()["data"]
    tl = client.get(f"/api/v1/development/tasks/{task['id']}/timeline").json()["data"]
    assert tl and all("stage" in s and "status" in s for s in tl)
    assert any(s.get("acting_employee") for s in tl)
