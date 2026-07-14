"""RBAC enforcement tests for the Quality Gate Engine."""

import pytest

from app.domain.roles import Role


def test_all_roles_can_read(client, as_role, quality_seeded):
    for role in Role:
        as_role(role)
        assert client.get("/api/v1/quality/rules").status_code == 200, role
        assert client.get("/api/v1/quality/founder-dashboard").status_code == 200, role


def test_unauthenticated_is_401(api_client, quality_seeded):
    assert api_client.get("/api/v1/quality/rules").status_code == 401


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 200),  # Directors may run/re-run gates
        (Role.DEPARTMENT_HEAD, 403),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_evaluate_requires_review(client, as_role, quality_seeded, role, expected):
    # Founder runs a task first so a gate target exists.
    task = client.post("/api/v1/development/run", json={"title": "RBAC gate task"}).json()["data"]
    as_role(role)
    resp = client.post(f"/api/v1/quality/tasks/{task['id']}/evaluate")
    assert resp.status_code == expected
