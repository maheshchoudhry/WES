"""API tests for the Department endpoints."""


def test_create_department(client, company):
    resp = client.post(
        "/api/v1/departments",
        json={"company_id": company["id"], "code": "DEPT-02", "name": "Engineering"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["code"] == "DEPT-02"


def test_department_unknown_company_returns_422(client):
    resp = client.post(
        "/api/v1/departments",
        json={
            "company_id": "00000000-0000-0000-0000-000000000000",
            "code": "DEPT-01",
            "name": "Product",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_department_code_returns_409(client, company, department):
    resp = client.post(
        "/api/v1/departments",
        json={"company_id": company["id"], "code": "DEPT-02", "name": "Different"},
    )
    assert resp.status_code == 409


def test_list_departments_filtered_by_company(client, company, department):
    resp = client.get(f"/api/v1/departments?company_id={company['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["id"] == department["id"]


def test_update_department(client, department):
    resp = client.patch(
        f"/api/v1/departments/{department['id']}", json={"name": "Platform Engineering"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Platform Engineering"


def test_delete_department(client, department):
    resp = client.delete(f"/api/v1/departments/{department['id']}")
    assert resp.status_code == 204
