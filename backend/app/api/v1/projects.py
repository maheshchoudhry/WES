"""Project REST endpoints (Sprint 07)."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_db, get_work_service, pagination, require_permission
from app.domain.roles import Permission
from app.schemas.work import ProjectCreate, ProjectUpdate
from app.services.project_decomposition import DecompositionService
from app.services.work import WorkService

router = APIRouter(prefix="/projects", tags=["projects"])
_read = Depends(require_permission(Permission.WORK_READ))
_write = Depends(require_permission(Permission.WORK_WRITE))


@router.get("", dependencies=[_read])
def list_projects(
    page: Pagination = Depends(pagination), service: WorkService = Depends(get_work_service)
) -> dict:
    items, total = service.list_projects(offset=page.offset, limit=page.limit)
    return {"data": items, "meta": {"total": total}}


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_project(
    payload: ProjectCreate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.create_project(payload)}


@router.get("/{project_id}", dependencies=[_read])
def get_project(project_id: uuid.UUID, service: WorkService = Depends(get_work_service)) -> dict:
    return {"data": service.get_project(project_id)}


@router.patch("/{project_id}", dependencies=[_write])
def update_project(
    project_id: uuid.UUID, payload: ProjectUpdate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.update_project(project_id, payload)}


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_write])
def delete_project(project_id: uuid.UUID, service: WorkService = Depends(get_work_service)) -> None:
    service.delete_project(project_id)


@router.get("/{project_id}/milestones", dependencies=[_read])
def project_milestones(
    project_id: uuid.UUID, service: WorkService = Depends(get_work_service)
) -> dict:
    items = service.list_milestones(project_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{project_id}/sprints", dependencies=[_read])
def project_sprints(
    project_id: uuid.UUID, service: WorkService = Depends(get_work_service)
) -> dict:
    items = service.list_sprints(project_id)
    return {"data": items, "meta": {"total": len(items)}}


# -- Autonomous decomposition (WP6) ---------------------------------------


@router.post("/{project_id}/decompose", dependencies=[_write])
def decompose_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """AI-CEO business analysis + automatic decomposition into epics -> sprints ->
    tasks with AI-employee assignment. Produces a plan awaiting Founder approval;
    does NOT begin implementation."""
    return {"data": DecompositionService(db).decompose(project_id)}


@router.get("/{project_id}/plan", dependencies=[_read])
def project_plan(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return {"data": DecompositionService(db).plan(project_id)}


@router.post("/{project_id}/approve-plan", dependencies=[_write])
def approve_project_plan(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Founder approval of the decomposition plan (unlocks execution phases)."""
    return {"data": DecompositionService(db).approve_plan(project_id)}
