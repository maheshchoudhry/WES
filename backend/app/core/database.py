"""Database engine, session factory, and FastAPI session dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# SQLite (local/tests) needs check_same_thread disabled for the FastAPI thread pool.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session (unit of work).

    Commits when the request handler completes successfully and rolls back if it
    raises, so each request is one atomic transaction.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
