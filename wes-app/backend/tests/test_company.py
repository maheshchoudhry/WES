def test_company_crud_lifecycle(client):
    created = client.post("/api/v1/companies", json={"name": "WES"})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "WES"
    assert body["legalType"] == "AI Engineering Company"
    company_id = body["id"]

    listed = client.get("/api/v1/companies")
    assert listed.status_code == 200
    page = listed.json()
    assert page["pagination"]["total"] == 1
    assert len(page["data"]) == 1

    fetched = client.get(f"/api/v1/companies/{company_id}")
    assert fetched.status_code == 200

    updated = client.patch(
        f"/api/v1/companies/{company_id}", json={"mission": "Build software"}
    )
    assert updated.status_code == 200
    assert updated.json()["mission"] == "Build software"

    deleted = client.delete(f"/api/v1/companies/{company_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/companies/{company_id}").status_code == 404


def test_company_validation_rejects_blank_name(client):
    resp = client.post("/api/v1/companies", json={"name": ""})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
