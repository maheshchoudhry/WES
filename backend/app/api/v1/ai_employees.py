"""AI Employee REST CRUD endpoints (Sprint 06)."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import Pagination, get_ai_org_service, pagination, require_permission
from app.domain.roles import Permission
from app.schemas.ai import AIEmployeeCreate, AIEmployeeUpdate
from app.services.ai_organization import AIOrganizationService

router = APIRouter(prefix="/ai-employees", tags=["ai-employees"])

_read = Depends(require_permission(Permission.AI_READ))
_update = Depends(require_permission(Permission.AI_UPDATE))
_manage = Depends(require_permission(Permission.AI_MANAGE))


@router.get("", dependencies=[_read])
def list_ai_employees(
    department_id: uuid.UUID | None = Query(default=None),
    role_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    page: Pagination = Depends(pagination),
    service: AIOrganizationService = Depends(get_ai_org_service),
) -> dict:
    items, total = service.list(
        department_id=department_id,
        role_id=role_id,
        status=status_filter,
        search=search,
        offset=page.offset,
        limit=page.limit,
    )
    return {"data": items, "meta": {"total": total}}


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[_manage])
def create_ai_employee(
    payload: AIEmployeeCreate,
    service: AIOrganizationService = Depends(get_ai_org_service),
) -> dict:
    return {"data": service.create(payload)}


@router.get("/{employee_id}", dependencies=[_read])
def get_ai_employee(
    employee_id: uuid.UUID,
    service: AIOrganizationService = Depends(get_ai_org_service),
) -> dict:
    return {"data": service.get(employee_id)}


@router.patch("/{employee_id}", dependencies=[_update])
def update_ai_employee(
    employee_id: uuid.UUID,
    payload: AIEmployeeUpdate,
    service: AIOrganizationService = Depends(get_ai_org_service),
) -> dict:
    return {"data": service.update(employee_id, payload)}


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_manage])
def delete_ai_employee(
    employee_id: uuid.UUID,
    service: AIOrganizationService = Depends(get_ai_org_service),
) -> None:
    service.delete(employee_id)
