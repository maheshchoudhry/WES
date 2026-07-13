import pytest


@pytest.fixture
def department_id(client):
    resp = client.post(
        "/api/v1/departments", json={"code": "ENG", "name": "Engineering"}
    )
    return resp.json()["id"]


def test_employee_crud_with_department(client, department_id):
    created = client.post(
        "/api/v1/employees",
        json={
            "employeeCode": "WES-EMP-001",
            "name": "Software Architect",
            "position": "Software Architect",
            "departmentId": department_id,
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["departmentName"] == "Engineering"
    emp_id = body["id"]

    listed = client.get(f"/api/v1/employees?departmentId={department_id}")
    assert listed.json()["pagination"]["total"] == 1

    updated = client.patch(
        f"/api/v1/employees/{emp_id}", json={"operationalState": "assigned"}
    )
    assert updated.json()["operationalState"] == "assigned"

    assert client.delete(f"/api/v1/employees/{emp_id}").status_code == 204


def test_employee_unique_code(client):
    payload = {
        "employeeCode": "WES-EMP-009",
        "name": "QA Engineer",
        "position": "QA Engineer",
    }
    assert client.post("/api/v1/employees", json=payload).status_code == 201
    dup = client.post("/api/v1/employees", json=payload)
    assert dup.status_code == 409


def test_employee_rejects_unknown_department(client):
    resp = client.post(
        "/api/v1/employees",
        json={
            "employeeCode": "WES-EMP-050",
            "name": "Ghost",
            "position": "Tester",
            "departmentId": 12345,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["message"] == "Department does not exist"


def test_system_metadata(client):
    resp = client.get("/api/v1/system/metadata")
    assert resp.status_code == 200
    assert "counts" in resp.json()["data"]
