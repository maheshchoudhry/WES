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


@pytest.fixture
def client(SessionFactory) -> TestClient:
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

    app.dependency_overrides[get_db] = _get_db_override
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
