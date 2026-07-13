"""RBAC enforcement tests for the AI Company Core endpoints."""

import pytest

from app.domain.roles import Role


def _ceo_and_refs(client):
    depts = client.get("/api/v1/ai-departments").json()["data"]
    roles = client.get("/api/v1/ai-roles").json()["data"]
    ceo = client.get("/api/v1/ai-employees?search=Ada").json()["data"][0]
    return depts, roles, ceo


def test_all_roles_can_read(client, as_role, ai_seeded):
    for role in Role:
        as_role(role)
        assert client.get("/api/v1/ai-employees").status_code == 200, role
        assert client.get("/api/v1/ai-roles").status_code == 200, role
        assert client.get("/api/v1/ai-departments").status_code == 200, role
        assert client.get("/api/v1/ai-org/summary").status_code == 200, role


def test_unauthenticated_is_401(api_client, ai_seeded):
    assert api_client.get("/api/v1/ai-employees").status_code == 401


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 201),
        (Role.DIRECTOR, 403),
        (Role.DEPARTMENT_HEAD, 403),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_create_requires_manage_permission(client, as_role, ai_seeded, role, expected):
    depts, roles, ceo = _ceo_and_refs(client)
    as_role(role)
    body = {
        "employee_code": f"AI-NEW-{role.value[:3]}",
        "name": f"New {role.value}",
        "department_id": depts[0]["id"],
        "role_id": next(r for r in roles if r["code"] == "BACKEND_ENGINEER")["id"],
        "manager_id": ceo["id"],
    }
    assert client.post("/api/v1/ai-employees", json=body).status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 200),
        (Role.DEPARTMENT_HEAD, 200),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_update_requires_update_permission(client, as_role, ai_seeded, role, expected):
    emp = client.get("/api/v1/ai-employees?search=Ritchie").json()["data"][0]
    as_role(role)
    resp = client.patch(f"/api/v1/ai-employees/{emp['id']}", json={"decision_scope": "changed"})
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 204),
        (Role.DIRECTOR, 403),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_delete_requires_manage_permission(client, as_role, ai_seeded, role, expected):
    emp = client.get("/api/v1/ai-employees?search=Strunk").json()["data"][0]
    as_role(role)
    assert client.delete(f"/api/v1/ai-employees/{emp['id']}").status_code == expected
