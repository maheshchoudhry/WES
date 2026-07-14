"""RBAC enforcement tests for the Organizational Knowledge Engine."""

import pytest

from app.domain.roles import Role


def test_all_roles_can_read(client, as_role, knowledge_seeded):
    for role in Role:
        as_role(role)
        assert client.get("/api/v1/knowledge/documents").status_code == 200, role
        assert client.get("/api/v1/knowledge/categories").status_code == 200, role
        assert client.get("/api/v1/knowledge/founder-dashboard").status_code == 200, role
        assert client.get("/api/v1/knowledge/graph").status_code == 200, role


def test_unauthenticated_is_401(api_client, knowledge_seeded):
    assert api_client.get("/api/v1/knowledge/documents").status_code == 401
    assert api_client.get("/api/v1/knowledge/ai-dashboard").status_code == 401


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 200),  # authors
        (Role.DEPARTMENT_HEAD, 200),  # authors
        (Role.EMPLOYEE, 403),  # read-only
        (Role.READ_ONLY, 403),
    ],
)
def test_create_document_requires_write(client, as_role, knowledge_seeded, role, expected):
    as_role(role)
    resp = client.post(
        "/api/v1/knowledge/documents",
        json={"title": "New Doc", "doc_type": "reference", "content": "x"},
    )
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "role,expected",
    [
        (Role.FOUNDER, 200),
        (Role.DIRECTOR, 200),  # approvers
        (Role.DEPARTMENT_HEAD, 403),  # can author but not approve
        (Role.EMPLOYEE, 403),
        (Role.READ_ONLY, 403),
    ],
)
def test_approve_requires_approver(client, as_role, knowledge_seeded, role, expected):
    doc = next(
        d
        for d in client.get("/api/v1/knowledge/documents").json()["data"]
        if d["code"] == "KB-0005"
    )
    as_role(role)
    resp = client.post(
        f"/api/v1/knowledge/documents/{doc['id']}/review",
        json={"decision": "approved", "comment": "ok"},
    )
    assert resp.status_code == expected


def test_employee_cannot_create_collection(client, as_role, knowledge_seeded):
    as_role(Role.EMPLOYEE)
    resp = client.post("/api/v1/knowledge/collections", json={"name": "Mine"})
    assert resp.status_code == 403
