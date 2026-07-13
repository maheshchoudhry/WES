"""Employee REST CRUD endpoints, including registration and department assignment."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import Pagination, get_employee_service, pagination, require_permission
from app.domain.roles import Permission
from app.schemas.employee import (
    EmployeeAssignDepartment,
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
)
from app.services.employee import EmployeeService

router = APIRouter(prefix="/employees", tags=["employees"])

_read = Depends(require_permission(Permission.EMPLOYEE_READ))
_write = Depends(require_permission(Permission.EMPLOYEE_WRITE))


@router.get("", dependencies=[_read])
def list_employees(
    company_id: uuid.UUID | None = Query(default=None),
    department_id: uuid.UUID | None = Query(default=None),
    page: Pagination = Depends(pagination),
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    items, total = service.list(
        company_id=company_id,
        department_id=department_id,
        offset=page.offset,
        limit=page.limit,
    )
    return {
        "data": [EmployeeRead.model_validate(i) for i in items],
        "meta": {"total": total},
    }


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def register_employee(
    payload: EmployeeCreate,
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    """Register (create) a new employee."""
    employee = service.register(payload)
    return {"data": EmployeeRead.model_validate(employee)}


@router.get("/{employee_id}", dependencies=[_read])
def get_employee(
    employee_id: uuid.UUID,
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    return {"data": EmployeeRead.model_validate(service.get(employee_id))}


@router.patch("/{employee_id}", dependencies=[_write])
def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeUpdate,
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    employee = service.update(employee_id, payload)
    return {"data": EmployeeRead.model_validate(employee)}


@router.put("/{employee_id}/department", dependencies=[_write])
def assign_department(
    employee_id: uuid.UUID,
    payload: EmployeeAssignDepartment,
    service: EmployeeService = Depends(get_employee_service),
) -> dict:
    """Assign the employee to a department (or clear it with a null id)."""
    employee = service.assign_department(employee_id, payload.department_id)
    return {"data": EmployeeRead.model_validate(employee)}


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_write])
def delete_employee(
    employee_id: uuid.UUID,
    service: EmployeeService = Depends(get_employee_service),
) -> None:
    service.delete(employee_id)
