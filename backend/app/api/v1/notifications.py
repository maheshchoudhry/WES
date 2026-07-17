"""Founder notification endpoints (Phase 4). Reuses dashboard read scope."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.domain.roles import Permission
from app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])
_read = Depends(require_permission(Permission.DASHBOARD_READ))


@router.get("", dependencies=[_read])
def list_notifications(
    unread: bool = Query(default=False), db: Session = Depends(get_db)
) -> dict:
    items = NotificationService(db).list(unread_only=unread)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/unread-count", dependencies=[_read])
def unread_count(db: Session = Depends(get_db)) -> dict:
    return {"data": {"unread": NotificationService(db).unread_count()}}


@router.post("/{notification_id}/read", dependencies=[_read])
def mark_read(notification_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return {"data": NotificationService(db).mark_read(notification_id)}


@router.post("/read-all", dependencies=[_read])
def mark_all_read(db: Session = Depends(get_db)) -> dict:
    return {"data": {"marked": NotificationService(db).mark_all_read()}}
