"""RBAC enforcement tests for the AI Orchestration Engine."""

import pytest

from app.domain.roles import Role


def test_all_roles_can_read(client, as_role, orch_seeded):
    for role in Role:
        as_role(role)
        assert client.get("/api/v1/providers").status_code == 200, role
        assert client.get("/api/v1/orchestration/runs").status_code == 200, role
        assert client.get("/api/v1/orchestration/founder-dashboard").status_code == 200, role


def test_unauthenticated_is_401(api_client, orch_seeded):
    assert api_client.get("/api/v1/providers").status_code == 401
    assert api_client.get("/api/v1/orchestration/runs").status_code == 401


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 403),
        (Role.DEPARTMENT_HEAD, 403),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_run_requires_founder(client, as_role, orch_seeded, role, expected):
    be = client.get("/api/v1/ai-employees?search=Ritchie").json()["data"][0]
    as_role(role)
    resp = client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "mock"}
    )
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_provider_settings_require_founder(client, as_role, orch_seeded, role, expected):
    openai = next(
        p for p in client.get("/api/v1/providers").json()["data"] if p["name"] == "openai"
    )
    as_role(role)
    resp = client.patch(f"/api/v1/providers/{openai['id']}/enabled", json={"enabled": True})
    assert resp.status_code == expected
