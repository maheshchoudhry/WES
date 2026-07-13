"""Department REST CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import Pagination, get_department_service, pagination, require_permission
from app.domain.roles import Permission
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services.department import DepartmentService

router = APIRouter(prefix="/departments", tags=["departments"])

_read = Depends(require_permission(Permission.DEPARTMENT_READ))
_write = Depends(require_permission(Permission.DEPARTMENT_WRITE))


@router.get("", dependencies=[_read])
def list_departments(
    company_id: uuid.UUID | None = Query(default=None),
    page: Pagination = Depends(pagination),
    service: DepartmentService = Depends(get_department_service),
) -> dict:
    items, total = service.list(company_id=company_id, offset=page.offset, limit=page.limit)
    return {
        "data": [DepartmentRead.model_validate(i) for i in items],
        "meta": {"total": total},
    }


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_department(
    payload: DepartmentCreate,
    service: DepartmentService = Depends(get_department_service),
) -> dict:
    department = service.create(payload)
    return {"data": DepartmentRead.model_validate(department)}


@router.get("/{department_id}", dependencies=[_read])
def get_department(
    department_id: uuid.UUID,
    service: DepartmentService = Depends(get_department_service),
) -> dict:
    return {"data": DepartmentRead.model_validate(service.get(department_id))}


@router.patch("/{department_id}", dependencies=[_write])
def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    service: DepartmentService = Depends(get_department_service),
) -> dict:
    department = service.update(department_id, payload)
    return {"data": DepartmentRead.model_validate(department)}


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_write])
def delete_department(
    department_id: uuid.UUID,
    service: DepartmentService = Depends(get_department_service),
) -> None:
    service.delete(department_id)
