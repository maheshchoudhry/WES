"""API tests for the Executive Dashboard aggregation endpoints."""


def _seed_org(client):
    company = client.post(
        "/api/v1/companies",
        json={"name": "WES", "slug": "wes", "company_type": "AI Company"},
    ).json()["data"]
    eng = client.post(
        "/api/v1/departments",
        json={"company_id": company["id"], "code": "DEPT-02", "name": "Engineering"},
    ).json()["data"]
    client.post(
        "/api/v1/departments",
        json={"company_id": company["id"], "code": "DEPT-04", "name": "Quality"},
    )
    architect = client.post(
        "/api/v1/employees",
        json={
            "company_id": company["id"],
            "department_id": eng["id"],
            "employee_code": "WES-EMP-004",
            "full_name": "Software Architect",
            "email": "arch@wes.studio",
            "position": "Software Architect",
            "authority": "lead",
            "status": "active",
        },
    ).json()["data"]
    client.post(
        "/api/v1/employees",
        json={
            "company_id": company["id"],
            "department_id": eng["id"],
            "reports_to_id": architect["id"],
            "employee_code": "WES-EMP-006",
            "full_name": "Backend Engineer",
            "email": "be@wes.studio",
            "position": "Backend Engineer",
            "authority": "operational",
            "status": "active",
        },
    )
    return company, eng, architect


def test_company_summary(client):
    _seed_org(client)
    body = client.get("/api/v1/dashboard/company-summary").json()["data"]
    assert body["name"] == "WES"
    assert body["department_count"] == 2
    assert body["employee_count"] == 2


def test_company_summary_null_when_empty(client):
    assert client.get("/api/v1/dashboard/company-summary").json()["data"] is None


def test_stats(client):
    _seed_org(client)
    stats = client.get("/api/v1/dashboard/stats").json()["data"]
    assert stats["totals"]["departments"] == 2
    assert stats["totals"]["employees"] == 2
    assert stats["totals"]["active_projects"] == 0
    assert stats["employees_by_status"]["active"] == 2
    assert stats["employees_by_authority"]["lead"] == 1
    assert stats["employees_by_authority"]["operational"] == 1


def test_department_stats_include_employee_counts(client):
    _, eng, _ = _seed_org(client)
    items = client.get("/api/v1/dashboard/departments").json()["data"]
    by_code = {d["code"]: d for d in items}
    assert by_code["DEPT-02"]["employee_count"] == 2
    assert by_code["DEPT-04"]["employee_count"] == 0


def test_employee_directory_resolves_manager_and_department(client):
    _seed_org(client)
    items = client.get("/api/v1/dashboard/employees").json()["data"]
    by_code = {e["employee_code"]: e for e in items}
    engineer = by_code["WES-EMP-006"]
    assert engineer["department_name"] == "Engineering"
    assert engineer["manager_name"] == "Software Architect"
    assert by_code["WES-EMP-004"]["manager_name"] is None


def test_recent_activity(client):
    _seed_org(client)
    resp = client.get("/api/v1/dashboard/activity?limit=5")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 5
    assert {i["entity_type"] for i in items} <= {"company", "department", "employee"}
    # Sorted by timestamp descending.
    timestamps = [i["timestamp"] for i in items]
    assert timestamps == sorted(timestamps, reverse=True)


def test_system_health(client):
    _seed_org(client)
    health = client.get("/api/v1/dashboard/health").json()["data"]
    assert health["api"] == "ok"
    assert health["database"] == "connected"
    assert health["companies"] == 1
    assert health["departments"] == 2
    assert health["employees"] == 2
