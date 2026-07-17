"""Phase 6 (WP8) — persistent long-term memory."""

import uuid

from app.services.memory import MemoryService


def test_remember_and_recall(db_session):
    mem = MemoryService(db_session)
    mem.remember(scope="org", kind="implementation", summary="Built the inventory API with caching")
    mem.remember(scope="org", kind="implementation", summary="Added a slug helper utility")
    db_session.flush()
    hits = mem.recall("inventory caching", scope="org")
    assert hits and "inventory" in hits[0]["summary"].lower()


def test_recall_persists_across_sessions(SessionFactory):
    eid = uuid.uuid4()
    db1 = SessionFactory()
    MemoryService(db1).remember(
        scope="employee", kind="decision", summary="Chose AST-safe edits", employee_id=eid
    )
    db1.commit()
    db1.close()
    # A brand-new session (as if after a restart) still recalls it.
    db2 = SessionFactory()
    hits = MemoryService(db2).list_for_employee(eid)
    assert any("AST-safe" in h["summary"] for h in hits)
    db2.close()


def test_workflow_writes_memory_and_next_task_recalls_it(client, quality_seeded):
    # First task → writes an org implementation memory.
    t1 = client.post(
        "/api/v1/development/run", json={"title": "Add a slug helper utility"}
    ).json()["data"]
    assert t1["status"] == "pr_ready"
    mem = client.get("/api/v1/company/memory?query=slug").json()["data"]
    assert any("slug" in m["summary"].lower() for m in mem)

    # Second, related task → its plan RECALLS the prior memory.
    t2 = client.post(
        "/api/v1/development/run", json={"title": "Add a slug formatter helper"}
    ).json()["data"]
    detail = client.get(f"/api/v1/development/tasks/{t2['id']}").json()["data"]
    assert "Recalled" in (detail["plan"]["summary"] or "")


def test_employee_workspace_includes_memory(client, quality_seeded, SessionFactory):
    from app.services.job_worker import run_once

    pid = client.post(
        "/api/v1/projects",
        json={"code": "MEM-1", "name": "Mem", "business_objective": "x", "deliverables": ["API"]},
    ).json()["data"]["id"]
    client.post(f"/api/v1/projects/{pid}/decompose")
    client.post(f"/api/v1/projects/{pid}/approve-plan")
    for _ in range(4):
        if not run_once(SessionFactory):
            break
    live = client.get("/api/v1/company/live").json()["data"]
    emp = next((e for e in live["employees"] if e["current_task"]), live["employees"][0])
    ws = client.get(f"/api/v1/company/employees/{emp['id']}/workspace").json()["data"]
    assert "memory" in ws  # employees carry recallable memory
