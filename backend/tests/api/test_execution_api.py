"""API + workflow tests for the AI Execution Engine."""


def _emp(client, name):
    return client.get(f"/api/v1/ai-employees?search={name}").json()["data"][0]


def test_libraries_seeded(client, exec_seeded):
    assert client.get("/api/v1/prompts").json()["meta"]["total"] == 5
    assert client.get("/api/v1/sops").json()["meta"]["total"] == 6
    assert client.get("/api/v1/decision-rules").json()["meta"]["total"] >= 12


def test_prompt_types_present(client, exec_seeded):
    types = {p["prompt_type"] for p in client.get("/api/v1/prompts").json()["data"]}
    assert types == {"system", "role", "task", "review", "escalation"}


def test_sop_categories_present(client, exec_seeded):
    cats = {s["category"] for s in client.get("/api/v1/sops").json()["data"]}
    assert cats == {"coding", "review", "testing", "deployment", "documentation", "security"}


def test_create_prompt(client, exec_seeded):
    resp = client.post(
        "/api/v1/prompts",
        json={"code": "PROMPT-NEW", "name": "New", "prompt_type": "task", "content": "Do it"},
    )
    assert resp.status_code == 201 and resp.json()["data"]["version"] == 1


def test_workspace_aggregate(client, exec_seeded):
    be = _emp(client, "Ritchie")
    ws = client.get(f"/api/v1/workspaces/{be['id']}").json()["data"]
    assert ws["employee"]["name"] == "Ritchie"
    assert len(ws["assigned_tasks"]) >= 1
    assert len(ws["queue"]) >= 1
    assert len(ws["history"]) >= 1
    assert len(ws["context_items"]) == 2
    assert "performance" in ws and "kpis" in ws


def test_execution_queue_seeded(client, exec_seeded):
    assert client.get("/api/v1/execution-queue").json()["meta"]["total"] == 5


def test_queue_advance_writes_history(client, exec_seeded):
    q = [x for x in client.get("/api/v1/execution-queue?status=queued").json()["data"]][0]
    before = client.get("/api/v1/execution-history").json()["meta"]["total"]
    client.post(f"/api/v1/execution-queue/{q['id']}/advance", json={"status": "in_progress"})
    r = client.post(
        f"/api/v1/execution-queue/{q['id']}/advance",
        json={"status": "completed", "output": "done"},
    )
    assert r.status_code == 200 and r.json()["data"]["status"] == "completed"
    after = client.get("/api/v1/execution-history").json()["meta"]["total"]
    assert after == before + 1


def test_review_decision(client, exec_seeded):
    rev = client.get("/api/v1/reviews?status=pending").json()["data"][0]
    r = client.post(
        f"/api/v1/reviews/{rev['id']}/decision", json={"status": "approved", "notes": "LGTM"}
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "approved"
    assert r.json()["data"]["reviewed_at"] is not None


def test_handoff_workflow_chain(client, exec_seeded):
    handoffs = client.get("/api/v1/handoffs").json()["data"]
    assert len(handoffs) == 8
    # Persisted, ordered chain Founder -> ... -> Founder Review.
    stages = [h["stage"] for h in sorted(handoffs, key=lambda x: x["sequence"])]
    assert stages[0] == "Founder -> AI CEO"
    assert "Technical Writer -> Founder Review" in stages[-1]
    # First four are completed, later ones pending.
    assert handoffs[0]["status"] == "completed"


def test_handoff_advance(client, exec_seeded):
    pending = [
        h for h in client.get("/api/v1/handoffs").json()["data"] if h["status"] == "pending"
    ][0]
    r = client.post(f"/api/v1/handoffs/{pending['id']}/advance", json={"status": "accepted"})
    assert r.status_code == 200 and r.json()["data"]["status"] == "accepted"


def test_execution_dashboards(client, exec_seeded):
    f = client.get("/api/v1/execution/founder-dashboard").json()["data"]
    assert f["ai_work_queue"] == 5
    assert f["pending_reviews"] == 1
    ai = client.get("/api/v1/execution/ai-dashboard").json()["data"]
    assert ai["execution_queue"] == 5
    assert ai["inbox"] == 8
