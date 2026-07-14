"""API + pipeline tests for the AI Orchestration Engine."""


def _backend(client):
    return client.get("/api/v1/ai-employees?search=Ritchie").json()["data"][0]


def test_providers_seeded(client, orch_seeded):
    providers = client.get("/api/v1/providers").json()["data"]
    by = {p["name"]: p for p in providers}
    assert set(by) == {"mock", "claude", "openai", "gemini", "openrouter", "ollama"}
    assert by["mock"]["enabled"] and by["mock"]["is_default"]
    assert by["mock"]["health"] == "healthy"
    assert by["claude"]["health"] == "unavailable"


def test_api_keys_are_masked(client, orch_seeded):
    claude = next(
        p for p in client.get("/api/v1/providers").json()["data"] if p["name"] == "claude"
    )
    assert claude["config"].get("api_key") in ("***", None)


def test_role_mappings_seeded(client, orch_seeded):
    mappings = client.get("/api/v1/providers/role-mappings").json()["data"]
    assert mappings.get("BACKEND_ENGINEER") == "mock"


def test_seed_created_sample_run(client, orch_seeded):
    runs = client.get("/api/v1/orchestration/runs").json()["data"]
    assert len(runs) >= 1
    assert runs[0]["provider_name"] == "mock"
    assert runs[0]["status"] == "completed"
    assert runs[0]["output"]


def test_run_stage_via_mock(client, orch_seeded):
    be = _backend(client)
    resp = client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "mock"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "completed"
    assert data["provider_name"] == "mock"
    assert data["duration_ms"] is not None


def test_provider_switching_unconfigured_fails(client, orch_seeded):
    be = _backend(client)
    resp = client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "claude"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "failed"
    assert "not configured" in (data["error"] or "").lower()


def test_conversation_and_memory_stored(client, orch_seeded):
    be = _backend(client)
    client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "mock"}
    )
    run = client.get("/api/v1/orchestration/runs").json()["data"][0]
    msgs = client.get(f"/api/v1/orchestration/threads/{run['thread_id']}/messages").json()
    # System + user prompt + assistant response are persisted.
    assert msgs["meta"]["total"] >= 3
    roles = {m["role"] for m in msgs["data"]}
    assert "assistant" in roles and "system" in roles


def test_review_run(client, orch_seeded):
    run = client.get("/api/v1/orchestration/runs?status=completed").json()["data"][0]
    resp = client.post(
        f"/api/v1/orchestration/runs/{run['id']}/review",
        json={"outcome": "approved", "notes": "ok"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["review_outcome"] == "approved"


def test_role_mapping_switch(client, orch_seeded):
    client.post(
        "/api/v1/providers/role-mappings",
        json={"role_code": "BACKEND_ENGINEER", "provider_name": "openai"},
    )
    assert (
        client.get("/api/v1/providers/role-mappings").json()["data"]["BACKEND_ENGINEER"] == "openai"
    )


def test_provider_enable_and_default(client, orch_seeded):
    openai = next(
        p for p in client.get("/api/v1/providers").json()["data"] if p["name"] == "openai"
    )
    client.patch(f"/api/v1/providers/{openai['id']}/enabled", json={"enabled": True})
    resp = client.post(f"/api/v1/providers/{openai['id']}/default")
    assert resp.status_code == 200 and resp.json()["data"]["is_default"] is True


def test_founder_dashboard(client, orch_seeded):
    d = client.get("/api/v1/orchestration/founder-dashboard").json()["data"]
    assert d["completed_executions"] >= 1
    assert d["token_usage"] > 0
    assert any(p["name"] == "mock" and p["health"] == "healthy" for p in d["providers"])


def test_ai_dashboard(client, orch_seeded):
    be = _backend(client)
    d = client.get(f"/api/v1/orchestration/ai-dashboard/{be['id']}").json()["data"]
    assert d["current_provider"] == "mock"
    assert d["memory_messages"] >= 3
    assert d["execution_history"] >= 1


def test_run_workflow(client, orch_seeded):
    task = client.get("/api/v1/tasks?search=WORLD-004").json()["data"][0]
    resp = client.post(
        "/api/v1/orchestration/run-workflow",
        json={"work_item_id": task["id"], "provider_name": "mock"},
    )
    assert resp.status_code == 200
    runs = resp.json()["data"]
    assert len(runs) == 8  # one per handoff stage
    assert all(r["status"] == "completed" for r in runs)
