"""Visibility phase — company observability from REAL runtime records."""

from app.services.job_worker import run_once


def _run_chain(client, SessionFactory):
    """Drive a real autonomous chain so there is genuine runtime data."""
    pid = client.post(
        "/api/v1/projects",
        json={
            "code": "VIS-1",
            "name": "Visibility Module",
            "business_objective": "Make the company visible",
            "deliverables": ["Widget API"],
        },
    ).json()["data"]["id"]
    client.post(f"/api/v1/projects/{pid}/decompose")
    client.post(f"/api/v1/projects/{pid}/approve-plan")
    # project_execution + a couple of dev workflows
    for _ in range(4):
        if not run_once(SessionFactory):
            break
    return pid


def test_live_reflects_real_employee_activity(client, quality_seeded, SessionFactory):
    _run_chain(client, SessionFactory)
    live = client.get("/api/v1/company/live").json()["data"]
    assert live["employees"], "employees must be listed"
    # Real derived state: every employee has a status + provider, some are working.
    assert all(e["status"] for e in live["employees"])
    assert all(e["provider"] for e in live["employees"])
    assert live["counts"]["working"] >= 1
    assert live["counts"]["tasks_in_progress"] >= 1


def test_timeline_events_come_from_runtime(client, quality_seeded, SessionFactory):
    _run_chain(client, SessionFactory)
    tl = client.get("/api/v1/company/timeline").json()["data"]
    types = {e["type"] for e in tl}
    assert "project_created" in types
    assert "stage" in types  # employees performed real stages
    assert any(e["actor"] == "Founder" for e in tl)
    # Events are timestamped and ordered (desc).
    ats = [e["at"] for e in tl]
    assert ats == sorted(ats, reverse=True)


def test_conversations_derived_from_real_handoffs(client, quality_seeded, SessionFactory):
    _run_chain(client, SessionFactory)
    convos = client.get("/api/v1/company/conversations").json()["data"]
    assert convos, "there must be real handoff-derived messages"
    for m in convos:
        assert m["from"] and m["to"] and m["from"] != m["to"]
        assert m["message"]


def test_employee_workspace_is_real(client, quality_seeded, SessionFactory):
    _run_chain(client, SessionFactory)
    # Pick an employee that has activity.
    live = client.get("/api/v1/company/live").json()["data"]
    working = next(e for e in live["employees"] if e["current_task"])
    ws = client.get(f"/api/v1/company/employees/{working['id']}/workspace").json()["data"]
    assert ws["profile"]["name"] == working["name"]
    assert ws["profile"]["provider"]
    assert ws["current"]["task"]  # a real current task
    assert ws["inbox"]  # real assigned work items
    assert ws["decisions"]  # real sessions this employee performed
    assert any(d["stage"] for d in ws["decisions"])
