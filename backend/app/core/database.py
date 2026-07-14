"""Database engine, session factory, and FastAPI session dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")
# SQLite (local/tests) needs check_same_thread disabled for the FastAPI thread pool.
# A busy_timeout lets concurrent writers wait instead of failing with "database is
# locked" (e.g. a streaming request open while another request writes).
_connect_args = {"check_same_thread": False, "timeout": 30} if _is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)


if _is_sqlite and not settings.database_url.endswith(":memory:") and "mode=memory" not in settings.database_url:

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _):
        # WAL allows a reader (e.g. an open stream) concurrently with a writer,
        # and busy_timeout waits on locks — production uses PostgreSQL.
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=30000")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()

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
