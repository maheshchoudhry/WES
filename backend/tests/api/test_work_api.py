"""API + CRUD + integration tests for the Work Management engine."""


def _project(client):
    return client.get("/api/v1/projects").json()["data"][0]


def test_seed_project(client, work_seeded):
    projects = client.get("/api/v1/projects").json()
    assert projects["meta"]["total"] == 1
    p = projects["data"][0]
    assert p["code"] == "PROJECT-001"
    assert p["name"] == "WORLD"
    assert p["owner_name"] == "Ada"
    assert p["task_count"] == 10


def test_sprints_progress(client, work_seeded):
    p = _project(client)
    sprints = client.get(f"/api/v1/projects/{p['id']}/sprints").json()["data"]
    assert len(sprints) == 3
    s1 = next(s for s in sprints if s["sprint_number"] == 1)
    assert s1["status"] == "completed" and s1["done_count"] == 2 and s1["velocity"] == 20


def test_tasks_list_and_filters(client, work_seeded):
    assert client.get("/api/v1/tasks").json()["meta"]["total"] == 10
    done = client.get("/api/v1/tasks?status=done").json()
    assert done["meta"]["total"] == 3
    search = client.get("/api/v1/tasks?search=dashboard").json()["data"]
    assert len(search) == 1 and search[0]["task_code"] == "WORLD-004"


def test_task_profile_resolves_names(client, work_seeded):
    t = client.get("/api/v1/tasks?search=WORLD-004").json()["data"][0]
    assert t["assigned_name"] == "Resig"
    assert t["reviewer_name"] == "Hopper"
    assert t["sprint_number"] == 3
    assert t["project_code"] == "PROJECT-001"


def test_kanban_columns(client, work_seeded):
    cols = client.get("/api/v1/work/kanban").json()["data"]
    by = {c["status"]: c["count"] for c in cols}
    assert [c["status"] for c in cols] == [
        "backlog",
        "planned",
        "assigned",
        "in_progress",
        "review",
        "testing",
        "done",
    ]
    assert by["done"] == 3


def test_task_crud(client, work_seeded):
    p = _project(client)
    resp = client.post(
        "/api/v1/tasks",
        json={"task_code": "WORLD-500", "title": "New feature", "project_id": p["id"]},
    )
    assert resp.status_code == 201
    tid = resp.json()["data"]["id"]
    upd = client.patch(f"/api/v1/tasks/{tid}", json={"status": "in_progress"})
    assert upd.status_code == 200 and upd.json()["data"]["status"] == "in_progress"
    assert client.delete(f"/api/v1/tasks/{tid}").status_code == 204


def test_duplicate_task_code_conflicts(client, work_seeded):
    p = _project(client)
    resp = client.post(
        "/api/v1/tasks",
        json={"task_code": "WORLD-001", "title": "Dup", "project_id": p["id"]},
    )
    assert resp.status_code == 409


def test_assignment_sets_assignee_and_status(client, work_seeded):
    p = _project(client)
    task = client.post(
        "/api/v1/tasks",
        json={"task_code": "WORLD-600", "title": "Assign me", "project_id": p["id"]},
    ).json()["data"]
    emp = client.get("/api/v1/ai-employees?search=Ritchie").json()["data"][0]
    resp = client.post(
        f"/api/v1/tasks/{task['id']}/assign",
        json={"ai_employee_id": emp["id"], "role": "assignee"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["assigned_name"] == "Ritchie"
    assert data["status"] == "assigned"  # backlog -> assigned
    # Assignment recorded.
    assignments = client.get(f"/api/v1/tasks/{task['id']}/assignments").json()
    assert assignments["meta"]["total"] == 1


def test_dependency_self_reference_rejected(client, work_seeded):
    task = client.get("/api/v1/tasks?search=WORLD-005").json()["data"][0]
    resp = client.post(
        f"/api/v1/tasks/{task['id']}/dependencies",
        json={"depends_on_id": task["id"], "type": "blocks"},
    )
    assert resp.status_code == 422


def test_seeded_dependency_present(client, work_seeded):
    task = client.get("/api/v1/tasks?search=WORLD-005").json()["data"][0]
    deps = client.get(f"/api/v1/tasks/{task['id']}/dependencies").json()["data"]
    assert len(deps) == 1 and deps[0]["depends_on_code"] == "WORLD-003"


def test_activity_timeline_records_events(client, work_seeded):
    p = _project(client)
    before = client.get(f"/api/v1/activity?project_id={p['id']}").json()["meta"]["total"]
    client.post(
        "/api/v1/tasks",
        json={"task_code": "WORLD-700", "title": "Logged", "project_id": p["id"]},
    )
    after = client.get(f"/api/v1/activity?project_id={p['id']}").json()["meta"]["total"]
    assert after == before + 1


def test_founder_summary(client, work_seeded):
    d = client.get("/api/v1/work/founder-summary").json()["data"]
    assert d["total_projects"] == 1
    assert d["total_tasks"] == 10
    assert d["blocked_tasks"] == 1
    assert d["velocity"] == 44  # 20 + 24 completed sprints
    assert d["tasks_by_status"]["done"] == 3


def test_ai_summary(client, work_seeded):
    d = client.get("/api/v1/work/ai-summary").json()["data"]
    assert d["completed_work"] == 3
    assert d["assigned_work"] >= 1
    assert "Engineering" in d["department_load"]
