"""Runtime database initialization.

Applies Alembic migrations (and optionally seeds) against the database the
application is configured to use. Paths are resolved from this file's location,
so initialization works regardless of the current working directory — the same
database the app serves is the one that gets migrated.

Usable two ways:
- On startup, via the FastAPI lifespan hook (see ``app.main``), controlled by
  ``WES_AUTO_MIGRATE`` / ``WES_SEED_ON_START``.
- As a CLI: ``python -m app.db.init`` (migrate + seed).
"""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.db.seed import seed

logger = logging.getLogger("app.db.init")

# app/db/init.py -> parents[2] == backend/
_BACKEND_DIR = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    """Build an Alembic config with absolute paths (cwd-independent)."""
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    # env.py injects the database URL from settings; keep it in sync here too.
    cfg.set_main_option("sqlalchemy.url", get_settings().database_url)
    return cfg


def run_migrations() -> None:
    """Apply all pending migrations up to head."""
    logger.info("Applying database migrations…")
    command.upgrade(_alembic_config(), "head")


def seed_if_requested() -> None:
    """Seed the initial WES organization (idempotent)."""
    db = SessionLocal()
    try:
        company = seed(db)
        if company is None:
            logger.info("Seed skipped: WES organization already present.")
        else:
            logger.info("Seeded initial WES organization.")
    finally:
        db.close()


def init_database(*, seed_data: bool = False) -> None:
    """Ensure the schema exists (migrate) and optionally seed."""
    run_migrations()
    if seed_data:
        seed_if_requested()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_database(seed_data=True)
    print("Database initialized (migrations applied, seed ensured).")


if __name__ == "__main__":
    main()
