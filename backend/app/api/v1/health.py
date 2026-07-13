"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness probe."""
    return {"data": {"status": "ok", "version": __version__}}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)) -> dict:
    """Readiness probe — verifies database connectivity."""
    db.execute(text("SELECT 1"))
    return {"data": {"status": "ready", "database": "connected"}}
