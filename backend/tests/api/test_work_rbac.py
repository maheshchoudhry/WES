"""RBAC enforcement tests for the Work Management endpoints."""

import pytest

from app.domain.roles import Role


def test_all_roles_can_read(client, as_role, work_seeded):
    for role in Role:
        as_role(role)
        assert client.get("/api/v1/projects").status_code == 200, role
        assert client.get("/api/v1/tasks").status_code == 200, role
        assert client.get("/api/v1/work/kanban").status_code == 200, role
        assert client.get("/api/v1/work/founder-summary").status_code == 200, role


def test_unauthenticated_is_401(api_client, work_seeded):
    assert api_client.get("/api/v1/projects").status_code == 401
    assert api_client.get("/api/v1/tasks").status_code == 401


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 201),
        (Role.DIRECTOR, 201),
        (Role.DEPARTMENT_HEAD, 201),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_task_write_permission(client, as_role, work_seeded, role, expected):
    p = client.get("/api/v1/projects").json()["data"][0]
    as_role(role)
    resp = client.post(
        "/api/v1/tasks",
        json={
            "task_code": f"WORLD-{role.value[:3].upper()}",
            "title": "New task",
            "project_id": p["id"],
        },
    )
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 201),
        (Role.DIRECTOR, 201),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_project_write_permission(client, as_role, work_seeded, role, expected):
    as_role(role)
    resp = client.post(
        "/api/v1/projects",
        json={"code": f"P-{role.value[:4]}", "name": f"Proj {role.value}"},
    )
    assert resp.status_code == expected
