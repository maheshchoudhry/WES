"""Phase 5 (WP5) — refresh rotation/revocation, rate limiting, audit + security log."""

import pytest

from app.core.config import get_settings
from app.core.rate_limit import reset_rate_limiter
from app.db.seed import seed

FOUNDER = "wes-emp-001@wes.studio"
PASSWORD = "WesOs2026!"


@pytest.fixture
def seeded(SessionFactory):
    db = SessionFactory()
    try:
        seed(db)
    finally:
        db.close()


def _login(client, email=FOUNDER, password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def _auth(access):
    return {"Authorization": f"Bearer {access}"}


def test_refresh_token_rotation_single_use(api_client, seeded):
    tokens = _login(api_client).json()["data"]["tokens"]
    old_refresh = tokens["refresh_token"]

    # First refresh works and returns a NEW refresh token.
    r1 = api_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r1.status_code == 200
    new_refresh = r1.json()["data"]["tokens"]["refresh_token"]
    assert new_refresh != old_refresh

    # Re-using the OLD (rotated) refresh token is rejected — single use.
    r2 = api_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r2.status_code == 401

    # The new one still works.
    r3 = api_client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert r3.status_code == 200


def test_logout_revokes_refresh_tokens(api_client, seeded):
    data = _login(api_client).json()["data"]
    access = data["tokens"]["access_token"]
    refresh = data["tokens"]["refresh_token"]

    api_client.post("/api/v1/auth/logout", headers=_auth(access))
    # The refresh token is revoked after logout.
    r = api_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 401


def test_login_and_failure_are_audited(api_client, seeded):
    access = _login(api_client).json()["data"]["tokens"]["access_token"]
    # A failed login records a security event.
    api_client.post("/api/v1/auth/login", json={"email": FOUNDER, "password": "wrong"})

    audit = api_client.get("/api/v1/audit", headers=_auth(access)).json()["data"]
    actions = {a["action"] for a in audit}
    assert "login" in actions
    security = api_client.get("/api/v1/audit?category=security", headers=_auth(access)).json()[
        "data"
    ]
    assert any(a["action"] == "login_failed" for a in security)


def test_pr_approval_is_audited(client, quality_seeded):
    task = client.post(
        "/api/v1/development/run", json={"title": "Add a slug helper utility"}
    ).json()["data"]
    client.post(f"/api/v1/development/tasks/{task['id']}/approve", json={"decision": "approved"})
    audit = client.get("/api/v1/audit").json()["data"]
    assert any(a["action"] == "pr_approval" for a in audit)


def test_rate_limiting_blocks_brute_force(api_client, seeded, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "rate_limit_enabled", True)
    monkeypatch.setattr(s, "rate_limit_auth", 3)
    reset_rate_limiter()
    try:
        codes = [
            api_client.post(
                "/api/v1/auth/login", json={"email": FOUNDER, "password": "x"}
            ).status_code
            for _ in range(6)
        ]
        assert 429 in codes  # brute force is throttled
    finally:
        reset_rate_limiter()
