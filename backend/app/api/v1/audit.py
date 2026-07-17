"""Audit log endpoints (WP5). Founder-only."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.domain.roles import Permission
from app.services.audit import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])
# Company-management scope (Founder/Director) governs audit visibility.
_read = Depends(require_permission(Permission.COMPANY_WRITE))


@router.get("", dependencies=[_read])
def list_audit(
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    items = AuditService(db).list(category=category)
    return {"data": items, "meta": {"total": len(items)}}
