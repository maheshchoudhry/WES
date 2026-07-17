"""Company observability endpoints (Visibility phase).

Read-only views over real runtime records so the Founder can watch the AI company
operate: live status, executive timeline, agent conversations, and per-employee
workspaces. Reuses the dashboard read scope.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.domain.roles import Permission
from app.services.company_observability import CompanyObservabilityService

router = APIRouter(prefix="/company", tags=["company"])
_read = Depends(require_permission(Permission.DASHBOARD_READ))


@router.get("/live", dependencies=[_read])
def live(db: Session = Depends(get_db)) -> dict:
    return {"data": CompanyObservabilityService(db).live()}


@router.get("/timeline", dependencies=[_read])
def timeline(limit: int = Query(default=120, le=300), db: Session = Depends(get_db)) -> dict:
    items = CompanyObservabilityService(db).timeline(limit=limit)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/conversations", dependencies=[_read])
def conversations(limit: int = Query(default=100, le=300), db: Session = Depends(get_db)) -> dict:
    items = CompanyObservabilityService(db).conversations(limit=limit)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/employees/{employee_id}/workspace", dependencies=[_read])
def employee_workspace(employee_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return {"data": CompanyObservabilityService(db).employee_workspace(employee_id)}


@router.get("/memory", dependencies=[_read])
def company_memory(
    query: str = Query(default=""),
    scope: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    from app.services.memory import MemoryService

    items = MemoryService(db).recall(query, scope=scope, limit=30)
    return {"data": items, "meta": {"total": len(items)}}
