"""RBAC enforcement tests for the Repository Intelligence Engine."""

import os

import pytest

from app.domain.roles import Role


def test_all_roles_can_read(client, as_role, repo_seeded):
    repo = client.get("/api/v1/repositories").json()["data"][0]
    for role in Role:
        as_role(role)
        assert client.get("/api/v1/repositories").status_code == 200, role
        assert client.get(f"/api/v1/repositories/{repo['id']}/dashboard").status_code == 200, role
        assert client.get(f"/api/v1/repositories/{repo['id']}/symbols").status_code == 200, role


def test_unauthenticated_is_401(api_client, repo_seeded):
    assert api_client.get("/api/v1/repositories").status_code == 401


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
def test_register_requires_founder(client, as_role, role, expected):
    as_role(role)
    resp = client.post(
        "/api/v1/repositories",
        json={"name": "Reg Test", "root_path": os.path.abspath("app/providers")},
    )
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [(Role.FOUNDER, 200), (Role.DIRECTOR, 403), (Role.EMPLOYEE, 403)],
)
def test_scan_requires_founder(client, as_role, repo_seeded, role, expected):
    repo = client.get("/api/v1/repositories").json()["data"][0]
    as_role(role)
    assert client.post(f"/api/v1/repositories/{repo['id']}/scan").status_code == expected
