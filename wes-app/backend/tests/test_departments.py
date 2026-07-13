def test_department_crud_and_unique_code(client):
    created = client.post(
        "/api/v1/departments",
        json={"code": "ENG", "name": "Engineering", "focus": "Build software"},
    )
    assert created.status_code == 201
    dept_id = created.json()["id"]

    duplicate = client.post(
        "/api/v1/departments", json={"code": "ENG", "name": "Engineering 2"}
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"

    listed = client.get("/api/v1/departments")
    assert listed.json()["pagination"]["total"] == 1

    updated = client.patch(
        f"/api/v1/departments/{dept_id}", json={"status": "inactive"}
    )
    assert updated.json()["status"] == "inactive"

    assert client.delete(f"/api/v1/departments/{dept_id}").status_code == 204


def test_department_not_found(client):
    resp = client.get("/api/v1/departments/999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
