"""RBAC enforcement tests for the Enterprise DevOps Platform."""

import pytest

from app.domain.roles import Role


def _approved_task(client):
    task = client.post("/api/v1/development/run", json={"title": "DevOps RBAC task"}).json()["data"]
    client.post(f"/api/v1/development/tasks/{task['id']}/approve", json={"decision": "approved"})
    return task


def test_all_roles_can_read(client, as_role, devops_seeded):
    for role in Role:
        as_role(role)
        assert client.get("/api/v1/devops/pipelines").status_code == 200, role
        assert client.get("/api/v1/devops/environments").status_code == 200, role
        assert client.get("/api/v1/devops/founder-dashboard").status_code == 200, role


def test_unauthenticated_is_401(api_client, devops_seeded):
    assert api_client.get("/api/v1/devops/pipelines").status_code == 401


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 200),  # Directors may run pipelines
        (Role.DEPARTMENT_HEAD, 403),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_run_pipeline_requires_execute(client, as_role, devops_seeded, role, expected):
    task = _approved_task(client)  # founder approves first
    as_role(role)
    resp = client.post(
        "/api/v1/devops/pipelines/run", json={"task_id": task["id"], "environment": "staging"}
    )
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [(Role.FOUNDER, 200), (Role.DIRECTOR, 403), (Role.EMPLOYEE, 403)],
)
def test_production_deploy_requires_founder(client, as_role, devops_seeded, role, expected):
    task = _approved_task(client)
    pipe = client.post(
        "/api/v1/devops/pipelines/run", json={"task_id": task["id"], "environment": "staging"}
    ).json()["data"]
    as_role(role)
    resp = client.post(f"/api/v1/devops/pipelines/{pipe['id']}/deploy-production")
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [(Role.FOUNDER, 200), (Role.DIRECTOR, 403)],
)
def test_rollback_requires_founder(client, as_role, devops_seeded, role, expected):
    task = _approved_task(client)
    pipe = client.post(
        "/api/v1/devops/pipelines/run", json={"task_id": task["id"], "environment": "staging"}
    ).json()["data"]
    as_role(role)
    resp = client.post(
        "/api/v1/devops/rollback",
        json={"environment": "staging", "to_release_id": pipe["release"]["id"]},
    )
    assert resp.status_code == expected
