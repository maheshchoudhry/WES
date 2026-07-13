"""Assignment and activity endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import Pagination, get_work_service, pagination, require_permission
from app.domain.roles import Permission
from app.schemas.work import AssignmentCreate
from app.services.work import WorkService

router = APIRouter(tags=["work"])
_read = Depends(require_permission(Permission.WORK_READ))
_write = Depends(require_permission(Permission.WORK_WRITE))


@router.post("/assignments", dependencies=[_write])
def create_assignment(
    work_item_id: uuid.UUID = Query(...),
    payload: AssignmentCreate = ...,
    service: WorkService = Depends(get_work_service),
) -> dict:
    """Assign an AI employee to a task (assignee or reviewer)."""
    return {"data": service.assign_task(work_item_id, payload)}


@router.get("/assignments", dependencies=[_read])
def list_assignments(
    work_item_id: uuid.UUID = Query(...), service: WorkService = Depends(get_work_service)
) -> dict:
    items = service.list_assignments(work_item_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/activity", dependencies=[_read])
def list_activity(
    project_id: uuid.UUID | None = Query(default=None),
    work_item_id: uuid.UUID | None = Query(default=None),
    page: Pagination = Depends(pagination),
    service: WorkService = Depends(get_work_service),
) -> dict:
    items, total = service.list_activity(
        project_id=project_id, work_item_id=work_item_id, offset=page.offset, limit=page.limit
    )
    return {"data": items, "meta": {"total": total}}
