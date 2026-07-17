"""Self-learning endpoints (WP9)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.domain.roles import Permission
from app.services.learning import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])
_read = Depends(require_permission(Permission.DASHBOARD_READ))


@router.get("/rules", dependencies=[_read])
def rules(kind: str | None = Query(default=None), db: Session = Depends(get_db)) -> dict:
    items = LearningService(db).rules(kind=kind)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/summary", dependencies=[_read])
def summary(db: Session = Depends(get_db)) -> dict:
    return {"data": LearningService(db).summary()}
