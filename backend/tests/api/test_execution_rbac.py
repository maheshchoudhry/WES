"""RBAC enforcement tests for the AI Execution Engine."""

import pytest

from app.domain.roles import Role


def test_all_roles_can_read(client, as_role, exec_seeded):
    for role in Role:
        as_role(role)
        assert client.get("/api/v1/prompts").status_code == 200, role
        assert client.get("/api/v1/sops").status_code == 200, role
        assert client.get("/api/v1/execution-queue").status_code == 200, role
        assert client.get("/api/v1/handoffs").status_code == 200, role
        assert client.get("/api/v1/execution/founder-dashboard").status_code == 200, role


def test_unauthenticated_is_401(api_client, exec_seeded):
    assert api_client.get("/api/v1/execution-queue").status_code == 401
    assert api_client.get("/api/v1/prompts").status_code == 401


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
def test_prompt_write_permission(client, as_role, exec_seeded, role, expected):
    as_role(role)
    resp = client.post(
        "/api/v1/prompts",
        json={
            "code": f"PROMPT-{role.value[:4].upper()}",
            "name": "Prompt",
            "prompt_type": "task",
            "content": "x",
        },
    )
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 200),
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_queue_advance_permission(client, as_role, exec_seeded, role, expected):
    q = client.get("/api/v1/execution-queue?status=queued").json()["data"][0]
    as_role(role)
    resp = client.post(f"/api/v1/execution-queue/{q['id']}/advance", json={"status": "in_progress"})
    assert resp.status_code == expected
