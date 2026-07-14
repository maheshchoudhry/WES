"""RBAC enforcement tests for the Autonomous Development Engine."""

import pytest

from app.domain.roles import Role


def test_all_roles_can_read(client, as_role, dev_seeded):
    for role in Role:
        as_role(role)
        assert client.get("/api/v1/development/tasks").status_code == 200, role
        assert client.get("/api/v1/development/founder-dashboard").status_code == 200, role


def test_unauthenticated_is_401(api_client, dev_seeded):
    assert api_client.get("/api/v1/development/tasks").status_code == 401


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 200),  # Directors may execute (monitor + run)
        (Role.DEPARTMENT_HEAD, 403),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_run_requires_execute(client, as_role, dev_seeded, role, expected):
    as_role(role)
    resp = client.post("/api/v1/development/tasks", json={"title": "RBAC probe task"})
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 403),  # only the Founder approves PRs
        (Role.EMPLOYEE, 403),
    ],
)
def test_approve_requires_founder(client, as_role, dev_seeded, role, expected):
    # Founder creates + runs a task first.
    tid = client.post("/api/v1/development/run", json={"title": "Approval RBAC task"}).json()[
        "data"
    ]["id"]
    as_role(role)
    resp = client.post(f"/api/v1/development/tasks/{tid}/approve", json={"decision": "approved"})
    assert resp.status_code == expected
