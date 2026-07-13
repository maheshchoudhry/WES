"""API tests for the Employee endpoints."""


def _register(client, company, **overrides):
    payload = {
        "company_id": company["id"],
        "employee_code": "WES-EMP-006",
        "full_name": "Backend Engineer",
        "email": "be@wes.studio",
        "position": "Backend Engineer",
        "authority": "operational",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/api/v1/employees", json=payload)


def test_register_employee(client, company):
    resp = _register(client, company)
    assert resp.status_code == 201
    assert resp.json()["data"]["employee_code"] == "WES-EMP-006"


def test_register_with_department(client, company, department):
    resp = _register(client, company, department_id=department["id"])
    assert resp.status_code == 201
    assert resp.json()["data"]["department_id"] == department["id"]


def test_duplicate_email_returns_409(client, company):
    _register(client, company)
    resp = _register(client, company, employee_code="WES-EMP-007")
    assert resp.status_code == 409


def test_invalid_email_returns_422(client, company):
    resp = _register(client, company, email="not-an-email")
    assert resp.status_code == 422


def test_assign_and_clear_department(client, company, department):
    emp = _register(client, company).json()["data"]
    resp = client.put(
        f"/api/v1/employees/{emp['id']}/department",
        json={"department_id": department["id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["department_id"] == department["id"]

    resp = client.put(
        f"/api/v1/employees/{emp['id']}/department", json={"department_id": None}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["department_id"] is None


def test_list_employees_filtered(client, company, department):
    _register(client, company, department_id=department["id"])
    resp = client.get(f"/api/v1/employees?department_id={department['id']}")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1


def test_update_and_delete_employee(client, company):
    emp = _register(client, company).json()["data"]
    resp = client.patch(
        f"/api/v1/employees/{emp['id']}", json={"status": "inactive"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "inactive"

    resp = client.delete(f"/api/v1/employees/{emp['id']}")
    assert resp.status_code == 204
