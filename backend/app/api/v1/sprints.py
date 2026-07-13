"""Sprint and Milestone REST endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_work_service, require_permission
from app.domain.roles import Permission
from app.schemas.work import MilestoneCreate, SprintCreate, SprintUpdate
from app.services.work import WorkService

router = APIRouter(tags=["work"])
_read = Depends(require_permission(Permission.WORK_READ))
_write = Depends(require_permission(Permission.WORK_WRITE))


@router.get("/sprints", dependencies=[_read])
def list_sprints(
    project_id: uuid.UUID = Query(...), service: WorkService = Depends(get_work_service)
) -> dict:
    items = service.list_sprints(project_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/sprints", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_sprint(payload: SprintCreate, service: WorkService = Depends(get_work_service)) -> dict:
    return {"data": service.create_sprint(payload)}


@router.patch("/sprints/{sprint_id}", dependencies=[_write])
def update_sprint(
    sprint_id: uuid.UUID, payload: SprintUpdate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.update_sprint(sprint_id, payload)}


@router.get("/milestones", dependencies=[_read])
def list_milestones(
    project_id: uuid.UUID = Query(...), service: WorkService = Depends(get_work_service)
) -> dict:
    items = service.list_milestones(project_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/milestones", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_milestone(
    payload: MilestoneCreate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.create_milestone(payload)}
