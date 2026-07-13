"""API tests for the Company endpoints."""


def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ok"


def test_create_and_get_company(client):
    resp = client.post(
        "/api/v1/companies",
        json={"name": "WES", "slug": "wes", "company_type": "AI Company"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["slug"] == "wes"

    resp = client.get(f"/api/v1/companies/{data['id']}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "WES"


def test_list_companies_has_meta(client, company):
    resp = client.get("/api/v1/companies")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert len(body["data"]) == 1


def test_invalid_slug_returns_422(client):
    resp = client.post(
        "/api/v1/companies",
        json={"name": "WES", "slug": "BAD SLUG", "company_type": "AI"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_slug_returns_409(client, company):
    resp = client.post(
        "/api/v1/companies",
        json={"name": "Another", "slug": "wes", "company_type": "AI"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


def test_get_missing_company_returns_404(client):
    resp = client.get("/api/v1/companies/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_update_company(client, company):
    resp = client.patch(f"/api/v1/companies/{company['id']}", json={"company_type": "Studio"})
    assert resp.status_code == 200
    assert resp.json()["data"]["company_type"] == "Studio"


def test_delete_company(client, company):
    resp = client.delete(f"/api/v1/companies/{company['id']}")
    assert resp.status_code == 204
    resp = client.get(f"/api/v1/companies/{company['id']}")
    assert resp.status_code == 404
