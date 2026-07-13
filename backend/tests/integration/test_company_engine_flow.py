"""Integration test: full Company Engine flow across all three modules.

Exercises the end-to-end lifecycle a developer would use to build the WES
organization through the REST API, verifying cross-entity business rules.
"""


def test_full_company_engine_lifecycle(client):
    # 1. Create the company.
    company = client.post(
        "/api/v1/companies",
        json={
            "name": "WORLD Engineering Studio",
            "slug": "wes",
            "company_type": "Independent AI Engineering Company",
            "purpose": "Design, manage, review, and build software projects.",
        },
    ).json()["data"]

    # 2. Create two departments.
    engineering = client.post(
        "/api/v1/departments",
        json={"company_id": company["id"], "code": "DEPT-02", "name": "Engineering"},
    ).json()["data"]
    quality = client.post(
        "/api/v1/departments",
        json={"company_id": company["id"], "code": "DEPT-04", "name": "Quality & Security"},
    ).json()["data"]

    # 3. Register a lead and assign to Engineering.
    architect = client.post(
        "/api/v1/employees",
        json={
            "company_id": company["id"],
            "department_id": engineering["id"],
            "employee_code": "WES-EMP-004",
            "full_name": "Software Architect",
            "email": "wes-emp-004@wes.studio",
            "position": "Software Architect",
            "authority": "lead",
            "status": "active",
        },
    ).json()["data"]

    # 4. Register an engineer reporting to the architect.
    engineer = client.post(
        "/api/v1/employees",
        json={
            "company_id": company["id"],
            "department_id": engineering["id"],
            "reports_to_id": architect["id"],
            "employee_code": "WES-EMP-006",
            "full_name": "Backend Engineer",
            "email": "wes-emp-006@wes.studio",
            "position": "Backend Engineer",
            "authority": "operational",
            "status": "active",
        },
    ).json()["data"]
    assert engineer["reports_to_id"] == architect["id"]

    # 5. Engineering now has two employees; it cannot be deleted.
    resp = client.delete(f"/api/v1/departments/{engineering['id']}")
    assert resp.status_code == 409

    # 6. Reassign both employees to Quality & Security, then delete Engineering.
    for emp in (architect, engineer):
        r = client.put(
            f"/api/v1/employees/{emp['id']}/department",
            json={"department_id": quality["id"]},
        )
        assert r.status_code == 200
    assert client.delete(f"/api/v1/departments/{engineering['id']}").status_code == 204

    # 7. The company still has a department and employees; it cannot be deleted.
    assert client.delete(f"/api/v1/companies/{company['id']}").status_code == 409

    # 8. Employee list scoped to the company reports both employees.
    listing = client.get(f"/api/v1/employees?company_id={company['id']}").json()
    assert listing["meta"]["total"] == 2
