"""API tests for role-based access control enforcement on protected endpoints."""

import pytest

from app.domain.roles import Role

ALL_ROLES = list(Role)


def test_all_roles_can_read(client, as_role, company, department):
    """Every authenticated role can read company/department/employee/dashboard."""
    for role in ALL_ROLES:
        as_role(role)
        assert client.get("/api/v1/departments").status_code == 200, role
        assert client.get("/api/v1/companies").status_code == 200, role
        assert client.get("/api/v1/employees").status_code == 200, role
        assert client.get("/api/v1/dashboard/stats").status_code == 200, role


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 201),
        (Role.DIRECTOR, 201),
        (Role.DEPARTMENT_HEAD, 403),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_department_write_permission(client, as_role, company, role, expected):
    as_role(role)
    resp = client.post(
        "/api/v1/departments",
        json={"company_id": company["id"], "code": f"D-{role.value[:3]}", "name": f"X {role.value}"},
    )
    assert resp.status_code == expected
    if expected == 403:
        assert resp.json()["error"]["code"] == "FORBIDDEN"


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
def test_employee_write_permission(client, as_role, company, role, expected):
    as_role(role)
    slug = role.value[:4]
    resp = client.post(
        "/api/v1/employees",
        json={
            "company_id": company["id"],
            "employee_code": f"EMP-{slug}",
            "full_name": f"User {slug}",
            "email": f"{slug}@wes.studio",
            "position": "Engineer",
        },
    )
    assert resp.status_code == expected


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
def test_company_write_permission(client, as_role, role, expected):
    as_role(role)
    resp = client.post(
        "/api/v1/companies",
        json={"name": f"Co {role.value}", "slug": f"co-{role.value}", "company_type": "AI"},
    )
    assert resp.status_code == expected
