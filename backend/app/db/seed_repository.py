"""Seed data for the Repository Intelligence Engine (Sprint 12).

Registers the WES backend application as a repository and runs one real scan so
the engine ships with genuine repository intelligence (files, symbols, imports,
architecture, metrics) that AI employees can retrieve. Idempotent: skips when the
repository already exists.

The scanned root is the backend ``app`` package — real source code — resolved
relative to this file, so it works regardless of the current working directory.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.work import Project
from app.services.repository_service import IndexerService, RepositoryService

# app/db/seed_repository.py -> app/ is two parents up from this file.
_APP_ROOT = Path(__file__).resolve().parents[1]


def seed_repository(db: Session) -> bool:
    """Register + scan the WES backend repository. Idempotent."""
    if db.scalar(select(Repository).where(Repository.slug == "wes-backend")):
        return False
    if not _APP_ROOT.exists():  # pragma: no cover - defensive
        return False

    project = db.scalar(select(Project).where(Project.code == "PROJECT-001"))
    service = RepositoryService(db)
    repo = service.register(
        "WES Backend",
        str(_APP_ROOT),
        description="The WES OS FastAPI backend application (self-hosted repository intelligence).",
        slug="wes-backend",
    )
    if project is not None:
        repo.project_id = project.id
    db.flush()
    IndexerService(db).scan(repo.id)
    db.flush()
    return True
