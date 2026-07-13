"""Work item (task) REST endpoints, incl. assignment, dependencies, comments."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import Pagination, get_work_service, pagination, require_permission
from app.domain.roles import Permission
from app.schemas.work import (
    AssignmentCreate,
    CommentCreate,
    DependencyCreate,
    WorkItemCreate,
    WorkItemUpdate,
)
from app.services.work import WorkService

router = APIRouter(prefix="/tasks", tags=["tasks"])
_read = Depends(require_permission(Permission.WORK_READ))
_write = Depends(require_permission(Permission.WORK_WRITE))


@router.get("", dependencies=[_read])
def list_tasks(
    project_id: uuid.UUID | None = Query(default=None),
    sprint_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    assigned_ai_employee_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    page: Pagination = Depends(pagination),
    service: WorkService = Depends(get_work_service),
) -> dict:
    items, total = service.list_tasks(
        offset=page.offset,
        limit=page.limit,
        project_id=project_id,
        sprint_id=sprint_id,
        status=status_filter,
        priority=priority,
        assigned_ai_employee_id=assigned_ai_employee_id,
        search=search,
    )
    return {"data": items, "meta": {"total": total}}


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_task(payload: WorkItemCreate, service: WorkService = Depends(get_work_service)) -> dict:
    return {"data": service.create_task(payload)}


@router.get("/{task_id}", dependencies=[_read])
def get_task(task_id: uuid.UUID, service: WorkService = Depends(get_work_service)) -> dict:
    return {"data": service.get_task(task_id)}


@router.patch("/{task_id}", dependencies=[_write])
def update_task(
    task_id: uuid.UUID, payload: WorkItemUpdate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.update_task(task_id, payload)}


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_write])
def delete_task(task_id: uuid.UUID, service: WorkService = Depends(get_work_service)) -> None:
    service.delete_task(task_id)


@router.post("/{task_id}/assign", dependencies=[_write])
def assign_task(
    task_id: uuid.UUID, payload: AssignmentCreate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.assign_task(task_id, payload)}


@router.get("/{task_id}/assignments", dependencies=[_read])
def task_assignments(task_id: uuid.UUID, service: WorkService = Depends(get_work_service)) -> dict:
    items = service.list_assignments(task_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{task_id}/dependencies", dependencies=[_read])
def task_dependencies(task_id: uuid.UUID, service: WorkService = Depends(get_work_service)) -> dict:
    items = service.list_dependencies(task_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/{task_id}/dependencies", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def add_dependency(
    task_id: uuid.UUID, payload: DependencyCreate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.add_dependency(task_id, payload)}


@router.get("/{task_id}/comments", dependencies=[_read])
def task_comments(task_id: uuid.UUID, service: WorkService = Depends(get_work_service)) -> dict:
    items = service.list_comments(task_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/{task_id}/comments", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def add_comment(
    task_id: uuid.UUID, payload: CommentCreate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.add_comment(task_id, payload)}
