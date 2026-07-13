"""API + CRUD + integration tests for the AI Company Core."""


def _ids(client):
    depts = client.get("/api/v1/ai-departments").json()["data"]
    roles = client.get("/api/v1/ai-roles").json()["data"]
    return depts, roles


def _role(roles, code):
    return next(r for r in roles if r["code"] == code)


def _dept(depts, code):
    return next(d for d in depts if d["code"] == code)


# --- listing / reads ----------------------------------------------------


def test_seed_counts(client, ai_seeded):
    assert len(_ids(client)[0]) == 3  # departments
    assert len(_ids(client)[1]) == 12  # roles
    listing = client.get("/api/v1/ai-employees").json()
    assert listing["meta"]["total"] == 12


def test_employee_profile_shape(client, ai_seeded):
    emp = client.get("/api/v1/ai-employees").json()["data"][0]
    for field in (
        "employee_code",
        "name",
        "department_name",
        "role_title",
        "authority",
        "decision_scope",
        "status",
        "version",
        "responsibilities",
        "capabilities",
        "kpis",
    ):
        assert field in emp
    assert emp["employee_code"] == "AI-EMP-001"
    assert emp["role_title"] == "AI CEO"
    assert emp["manager_id"] is None


def test_filter_by_department(client, ai_seeded):
    depts, _ = _ids(client)
    eng = _dept(depts, "AI-DEPT-03")
    resp = client.get(f"/api/v1/ai-employees?department_id={eng['id']}")
    assert resp.json()["meta"]["total"] == 8


def test_search(client, ai_seeded):
    resp = client.get("/api/v1/ai-employees?search=ada")
    data = resp.json()["data"]
    assert len(data) == 1 and data[0]["name"] == "Ada"


def test_pagination(client, ai_seeded):
    resp = client.get("/api/v1/ai-employees?page=1&page_size=5")
    body = resp.json()
    assert len(body["data"]) == 5 and body["meta"]["total"] == 12


# --- create / business rules --------------------------------------------


def test_create_requires_manager_for_non_ceo(client, ai_seeded):
    depts, roles = _ids(client)
    resp = client.post(
        "/api/v1/ai-employees",
        json={
            "employee_code": "AI-EMP-100",
            "name": "New Engineer",
            "department_id": _dept(depts, "AI-DEPT-03")["id"],
            "role_id": _role(roles, "BACKEND_ENGINEER")["id"],
            # no manager_id
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_with_manager(client, ai_seeded):
    depts, roles = _ids(client)
    ceo = client.get("/api/v1/ai-employees?search=Ada").json()["data"][0]
    resp = client.post(
        "/api/v1/ai-employees",
        json={
            "employee_code": "AI-EMP-101",
            "name": "New Engineer",
            "department_id": _dept(depts, "AI-DEPT-03")["id"],
            "role_id": _role(roles, "BACKEND_ENGINEER")["id"],
            "manager_id": ceo["id"],
            "capabilities": ["backend_development", "code_review"],
            "responsibilities": ["Build services"],
            "kpis": [{"name": "Throughput", "target": "10", "unit": "/sprint"}],
        },
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["manager_name"] == "Ada"
    assert {c["code"] for c in data["capabilities"]} == {"backend_development", "code_review"}
    assert data["responsibilities"] == ["Build services"]
    assert data["version"] == 1


def test_duplicate_code_conflicts(client, ai_seeded):
    depts, roles = _ids(client)
    ceo = client.get("/api/v1/ai-employees?search=Ada").json()["data"][0]
    body = {
        "employee_code": "AI-EMP-001",  # already seeded
        "name": "Dup",
        "department_id": _dept(depts, "AI-DEPT-03")["id"],
        "role_id": _role(roles, "BACKEND_ENGINEER")["id"],
        "manager_id": ceo["id"],
    }
    assert client.post("/api/v1/ai-employees", json=body).status_code == 409


def test_unknown_role_rejected(client, ai_seeded):
    depts, _ = _ids(client)
    ceo = client.get("/api/v1/ai-employees?search=Ada").json()["data"][0]
    resp = client.post(
        "/api/v1/ai-employees",
        json={
            "employee_code": "AI-EMP-102",
            "name": "X",
            "department_id": _dept(depts, "AI-DEPT-03")["id"],
            "role_id": "00000000-0000-0000-0000-000000000000",
            "manager_id": ceo["id"],
        },
    )
    assert resp.status_code == 422


# --- update -------------------------------------------------------------


def test_update_bumps_version_and_replaces_children(client, ai_seeded):
    emp = client.get("/api/v1/ai-employees?search=Ritchie").json()["data"][0]
    resp = client.patch(
        f"/api/v1/ai-employees/{emp['id']}",
        json={"decision_scope": "Expanded scope", "responsibilities": ["Only this one"]},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["decision_scope"] == "Expanded scope"
    assert data["responsibilities"] == ["Only this one"]
    assert data["version"] == emp["version"] + 1


def test_cannot_report_to_self(client, ai_seeded):
    emp = client.get("/api/v1/ai-employees?search=Ritchie").json()["data"][0]
    resp = client.patch(f"/api/v1/ai-employees/{emp['id']}", json={"manager_id": emp["id"]})
    assert resp.status_code == 422


# --- soft delete --------------------------------------------------------


def test_soft_delete_hides_and_promotes_reports(client, ai_seeded):
    # Delete the CTO (Turing); its reports should be promoted to the CEO.
    cto = client.get("/api/v1/ai-employees?search=Turing").json()["data"][0]
    architect = client.get("/api/v1/ai-employees?search=Hopper").json()["data"][0]
    assert architect["manager_name"] == "Turing"

    assert client.delete(f"/api/v1/ai-employees/{cto['id']}").status_code == 204
    # Gone from listings.
    assert client.get("/api/v1/ai-employees?search=Turing").json()["meta"]["total"] == 0
    assert client.get(f"/api/v1/ai-employees/{cto['id']}").status_code == 404
    assert client.get("/api/v1/ai-employees").json()["meta"]["total"] == 11
    # Report promoted to the CTO's former manager (the CEO).
    promoted = client.get(f"/api/v1/ai-employees/{architect['id']}").json()["data"]
    assert promoted["manager_name"] == "Ada"


# --- org endpoints ------------------------------------------------------


def test_org_chart(client, ai_seeded):
    roots = client.get("/api/v1/ai-org/chart").json()["data"]
    assert len(roots) == 1
    assert roots[0]["name"] == "Ada"
    assert len(roots[0]["reports"]) == 2


def test_department_view(client, ai_seeded):
    view = client.get("/api/v1/ai-org/departments").json()["data"]
    by_code = {d["code"]: d for d in view}
    assert by_code["AI-DEPT-03"]["employee_count"] == 8


def test_summary_health(client, ai_seeded):
    summary = client.get("/api/v1/ai-org/summary").json()["data"]
    assert summary["total_employees"] == 12
    assert summary["department_count"] == 3
    assert summary["ceo_present"] is True
    assert summary["organization_health"] == "healthy"
