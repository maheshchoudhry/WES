"""Provider Platform tests (Sprint 11): secrets, connection, models, budget,
cost, metrics, failover, retry, streaming, and security."""

import pytest

from app.providers.base import (
    BaseProvider,
    ExecutionRequest,
    ExecutionResult,
    ProviderHealth,
    RateLimitError,
)
from app.providers.registry import ProviderRegistry


# -- a controllable provider registered once for retry/rate-limit tests -----
class FlakyProvider(BaseProvider):
    name = "flaky"
    default_model = "flaky-1"
    attempts = 0

    def initialize(self):
        self._initialized = True

    def health(self):
        return ProviderHealth(status="healthy", detail="flaky ready")

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        FlakyProvider.attempts += 1
        if FlakyProvider.attempts == 1:
            raise RateLimitError("flaky rate limited", retry_after=0)
        return ExecutionResult(
            output="recovered after retry",
            provider=self.name,
            model=self.default_model,
            prompt_tokens=3,
            completion_tokens=3,
            total_tokens=6,
            cost=0.0,
            currency="USD",
            latency_ms=1,
        )

    def stream(self, request):
        yield "recovered "

    def cancel(self, run_id):
        return True


ProviderRegistry.register("flaky", FlakyProvider)


def _backend(client):
    return client.get("/api/v1/ai-employees?search=Ritchie").json()["data"][0]


def _provider(client, name):
    return next(p for p in client.get("/api/v1/providers").json()["data"] if p["name"] == name)


# -- secrets & security ----------------------------------------------------


def test_set_secret_is_encrypted_and_masked(client, orch_seeded, db_session):
    from app.models.provider_platform import ProviderSecret

    claude = _provider(client, "claude")
    plaintext = "sk-ant-realsecret-987654"
    resp = client.post(f"/api/v1/providers/{claude['id']}/secret", json={"value": plaintext})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["has_secret"] is True
    assert data["secret_hint"] and data["secret_hint"].endswith("7654")

    # Plaintext never appears in any API response.
    all_providers = client.get("/api/v1/providers").text
    assert plaintext not in all_providers

    # Stored ciphertext is not the plaintext.
    row = db_session.query(ProviderSecret).first()
    assert row is not None and plaintext not in row.ciphertext


def test_secret_change_is_audited(client, orch_seeded):
    claude = _provider(client, "claude")
    client.post(f"/api/v1/providers/{claude['id']}/secret", json={"value": "sk-audit-12345678"})
    events = client.get("/api/v1/providers/events").json()["data"]
    assert any(e["event_type"] in ("secret.set", "secret.rotated") for e in events)


def test_short_secret_rejected(client, orch_seeded):
    claude = _provider(client, "claude")
    resp = client.post(f"/api/v1/providers/{claude['id']}/secret", json={"value": "short"})
    assert resp.status_code == 422


# -- connection testing ----------------------------------------------------


def test_connection_mock_ok(client, orch_seeded):
    mock = _provider(client, "mock")
    resp = client.post(f"/api/v1/providers/{mock['id']}/test")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ok"] is True and data["status"] == "healthy"


def test_connection_unconfigured_reports_unavailable(client, orch_seeded):
    claude = _provider(client, "claude")
    data = client.post(f"/api/v1/providers/{claude['id']}/test").json()["data"]
    assert data["ok"] is False and data["status"] == "unavailable"


# -- models ----------------------------------------------------------------


def test_models_seeded_and_selectable(client, orch_seeded):
    claude = _provider(client, "claude")
    models = client.get(f"/api/v1/providers/{claude['id']}/models").json()["data"]
    codes = {m["code"] for m in models}
    assert {"claude-opus-4-8", "claude-sonnet-5"} <= codes

    resp = client.post(
        f"/api/v1/providers/{claude['id']}/active-model", json={"model_code": "claude-sonnet-5"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["active_model"] == "claude-sonnet-5"


def test_add_model(client, orch_seeded):
    openai = _provider(client, "openai")
    resp = client.post(
        f"/api/v1/providers/{openai['id']}/models",
        json={"code": "gpt-5", "display_name": "GPT-5", "input_cost_per_1k": 0.003},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["code"] == "gpt-5"


# -- budget ----------------------------------------------------------------


def test_budget_config_and_status(client, orch_seeded):
    status = client.get("/api/v1/providers/budget").json()["data"]
    assert "daily_spent" in status and "config" in status
    resp = client.put(
        "/api/v1/providers/budget",
        json={"daily_cost_limit": 10.0, "warning_threshold": 0.5, "hard_stop": True},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["config"]["daily_cost_limit"] == 10.0


def test_budget_hard_stop_blocks_execution(client, orch_seeded):
    be = _backend(client)
    # A per-run token cap of 1 with hard stop blocks any real prompt.
    client.put("/api/v1/providers/budget", json={"max_tokens": 1, "hard_stop": True})
    resp = client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "mock"}
    )
    data = resp.json()["data"]
    assert data["status"] == "failed"
    assert "budget" in (data["error"] or "").lower()


def test_budget_soft_limit_allows_with_warning(client, orch_seeded):
    be = _backend(client)
    client.put("/api/v1/providers/budget", json={"max_tokens": 1, "hard_stop": False})
    resp = client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "mock"}
    )
    assert resp.json()["data"]["status"] == "completed"  # not hard-stopped


# -- failover --------------------------------------------------------------


def test_failover_switches_provider(client, orch_seeded):
    be = _backend(client)
    claude = _provider(client, "claude")
    # Enable claude (no key -> will fail) and route the role to it.
    client.patch(f"/api/v1/providers/{claude['id']}/enabled", json={"enabled": True})
    client.post(
        "/api/v1/providers/role-mappings",
        json={"role_code": "BACKEND_ENGINEER", "provider_name": "claude"},
    )
    # Auto-resolved run (no explicit provider) fails over from claude to mock.
    resp = client.post("/api/v1/orchestration/run", json={"ai_employee_id": be["id"]})
    data = resp.json()["data"]
    assert data["status"] == "completed"
    assert data["provider_name"] == "mock"
    events = client.get("/api/v1/providers/events").json()["data"]
    assert any(e["event_type"] == "failover.switched" for e in events)


# -- retry / rate limit ----------------------------------------------------


def test_rate_limit_retry_recovers(client, orch_seeded, db_session):
    from app.models.orchestration import AIProvider, RetryHistory

    FlakyProvider.attempts = 0
    db_session.add(
        AIProvider(name="flaky", display_name="Flaky", enabled=True, default_model="flaky-1")
    )
    db_session.commit()
    be = _backend(client)
    resp = client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "flaky"}
    )
    data = resp.json()["data"]
    assert data["status"] == "completed"
    assert "recovered" in data["output"]
    # First attempt was rate-limited, second succeeded.
    statuses = {r.status for r in db_session.query(RetryHistory).all()}
    assert "rate_limited" in statuses and "succeeded" in statuses


# -- streaming -------------------------------------------------------------


def test_streaming_emits_tokens_and_done(client, orch_seeded):
    be = _backend(client)
    resp = client.post(
        "/api/v1/orchestration/stream",
        json={"ai_employee_id": be["id"], "provider_name": "mock"},
    )
    assert resp.status_code == 200
    body = resp.text
    assert "event: start" in body
    assert "event: token" in body
    assert "event: done" in body


def test_cancel_endpoint(client, orch_seeded):
    run = client.get("/api/v1/orchestration/runs").json()["data"][0]
    resp = client.post(f"/api/v1/orchestration/runs/{run['id']}/cancel")
    assert resp.status_code == 200
    assert resp.json()["data"]["cancelled"] is True


# -- cost / metrics / dashboard --------------------------------------------


def test_cost_aggregation(client, orch_seeded):
    be = _backend(client)
    client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "mock"}
    )
    by_provider = client.get("/api/v1/providers/cost?group_by=provider").json()["data"]
    assert any(row["label"] == "mock" and row["tokens"] > 0 for row in by_provider)
    by_employee = client.get("/api/v1/providers/cost?group_by=employee").json()["data"]
    assert len(by_employee) >= 1


def test_metrics_and_events(client, orch_seeded):
    metrics = client.get("/api/v1/providers/metrics").json()["data"]
    assert any(m["provider"] == "mock" for m in metrics)
    # A connection test records an audit event.
    mock = _provider(client, "mock")
    client.post(f"/api/v1/providers/{mock['id']}/test")
    events = client.get("/api/v1/providers/events").json()
    assert events["meta"]["total"] >= 1
    assert any(e["event_type"] == "connection.tested" for e in events["data"])


def test_platform_dashboard(client, orch_seeded):
    d = client.get("/api/v1/providers/dashboard").json()["data"]
    assert "providers" in d and "budget" in d and "metrics" in d
    assert any(p["name"] == "mock" for p in d["providers"])
    assert "cost_by_provider" in d


def test_platform_ai_dashboard(client, orch_seeded):
    be = _backend(client)
    d = client.get(f"/api/v1/providers/ai-dashboard/{be['id']}").json()["data"]
    assert d["current_provider"] == "mock"
    assert "current_model" in d and "tokens" in d


def test_monitor_all(client, orch_seeded):
    results = client.post("/api/v1/providers/monitor").json()["data"]
    names = {r["provider"] for r in results}
    assert "mock" in names
    assert any(r["provider"] == "mock" and r["ok"] for r in results)


def test_priority_and_failover_order(client, orch_seeded):
    openai = _provider(client, "openai")
    resp = client.post(f"/api/v1/providers/{openai['id']}/priority", json={"priority": 5})
    assert resp.status_code == 200
    assert resp.json()["data"]["priority"] == 5


# -- RBAC ------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/api/v1/providers/budget", "/api/v1/providers/dashboard"])
def test_reads_allowed_for_all_roles(client, as_role, orch_seeded, path):
    from app.domain.roles import Role

    for role in Role:
        as_role(role)
        assert client.get(path).status_code == 200, (role, path)


def test_secret_write_requires_founder(client, as_role, orch_seeded):
    from app.domain.roles import Role

    claude = _provider(client, "claude")
    as_role(Role.DIRECTOR)
    resp = client.post(f"/api/v1/providers/{claude['id']}/secret", json={"value": "sk-nope-123456"})
    assert resp.status_code == 403
