"""API tests for the authentication endpoints (real login/JWT flow)."""

import pytest

from app.db.seed import seed

FOUNDER_EMAIL = "wes-emp-001@wes.studio"
READONLY_EMAIL = "wes-emp-013@wes.studio"
PASSWORD = "WesOs2026!"


@pytest.fixture
def seeded(SessionFactory):
    """Seed the WES organization (with roles + passwords) into the test DB."""
    db = SessionFactory()
    try:
        seed(db)
    finally:
        db.close()


def _login(client, email=FOUNDER_EMAIL, password=PASSWORD, remember=False):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "remember": remember},
    )


def test_login_success_returns_user_and_tokens(api_client, seeded):
    resp = _login(api_client)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["user"]["role"] == "founder"
    assert data["tokens"]["access_token"]
    assert data["tokens"]["refresh_token"]
    assert data["tokens"]["token_type"] == "bearer"


def test_login_wrong_password_returns_401(api_client, seeded):
    resp = _login(api_client, password="nope")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_unknown_email_returns_401(api_client, seeded):
    resp = _login(api_client, email="ghost@wes.studio")
    assert resp.status_code == 401


def test_me_requires_token(api_client, seeded):
    assert api_client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_current_user(api_client, seeded):
    token = _login(api_client).json()["data"]["tokens"]["access_token"]
    resp = api_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == FOUNDER_EMAIL


def test_protected_endpoint_requires_auth(api_client, seeded):
    assert api_client.get("/api/v1/dashboard/stats").status_code == 401
    token = _login(api_client).json()["data"]["tokens"]["access_token"]
    ok = api_client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200


def test_refresh_issues_new_access_token(api_client, seeded):
    refresh = _login(api_client).json()["data"]["tokens"]["refresh_token"]
    resp = api_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["data"]["tokens"]["access_token"]


def test_logout_invalidates_refresh_token(api_client, seeded):
    tokens = _login(api_client).json()["data"]["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Logout bumps the refresh token version.
    assert api_client.post("/api/v1/auth/logout", headers=headers).status_code == 200

    # The old refresh token is now revoked.
    resp = api_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


def test_invalid_bearer_token_returns_401(api_client, seeded):
    resp = api_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_remember_me_login_succeeds(api_client, seeded):
    resp = _login(api_client, email=READONLY_EMAIL, remember=True)
    assert resp.status_code == 200
    assert resp.json()["data"]["user"]["role"] == "read_only"
