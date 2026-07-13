"""Pytest fixtures.

Each test runs against a fresh in-memory SQLite database (sanctioned for tests
by Blueprint Vol. 06). A StaticPool keeps a single shared connection so the app
and the test see the same data.
"""

import os

# Disable startup auto-migration/seeding before the app is imported: tests manage
# their own isolated in-memory schema and must not touch the configured database.
os.environ["WES_AUTO_MIGRATE"] = "false"
os.environ["WES_SEED_ON_START"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def SessionFactory(engine):
    return sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
    )


@pytest.fixture
def db_session(SessionFactory) -> Session:
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


def _db_override_factory(SessionFactory):
    def _get_db_override():
        db = SessionFactory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return _get_db_override


import uuid  # noqa: E402

from app.api.deps import CurrentUser, get_current_user  # noqa: E402
from app.domain.roles import Role  # noqa: E402


def _principal(role: Role) -> CurrentUser:
    return CurrentUser(
        id=uuid.uuid4(),
        email=f"{role.value}@wes.studio",
        role=role,
        full_name=f"Test {role.value}",
        department_id=None,
    )


@pytest.fixture
def client(SessionFactory) -> TestClient:
    """Authenticated client acting as a Founder (full access).

    Existing Company Engine tests use this and continue to pass, now under auth.
    """
    app.dependency_overrides[get_db] = _db_override_factory(SessionFactory)
    app.dependency_overrides[get_current_user] = lambda: _principal(Role.FOUNDER)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def as_role(client):
    """Return a setter that switches the current user's role on the client."""

    def _set(role: Role) -> None:
        app.dependency_overrides[get_current_user] = lambda: _principal(role)

    return _set


@pytest.fixture
def api_client(SessionFactory) -> TestClient:
    """Client WITHOUT an auth override — exercises the real login/JWT flow."""
    app.dependency_overrides[get_db] = _db_override_factory(SessionFactory)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def company(client) -> dict:
    """A persisted company, returned as its API representation."""
    resp = client.post(
        "/api/v1/companies",
        json={
            "name": "WORLD Engineering Studio",
            "slug": "wes",
            "company_type": "Independent AI Engineering Company",
            "purpose": "Build software",
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]


@pytest.fixture
def department(client, company) -> dict:
    resp = client.post(
        "/api/v1/departments",
        json={
            "company_id": company["id"],
            "code": "DEPT-02",
            "name": "Engineering",
            "focus": "Build the software",
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]
