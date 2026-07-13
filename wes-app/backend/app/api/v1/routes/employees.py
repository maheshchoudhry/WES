"""Employee CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import Pagination
from app.db.session import get_db
from app.models.employee import Employee
from app.schemas.common import Page, PageMeta
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services.employee import EmployeeService

router = APIRouter(prefix="/employees", tags=["employees"])


def _to_read(employee: Employee) -> EmployeeRead:
    read = EmployeeRead.model_validate(employee)
    read.department_name = employee.department.name if employee.department else None
    return read


@router.get("", response_model=Page[EmployeeRead])
def list_employees(
    page: Pagination = Depends(),
    department_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> Page:
    items, total = EmployeeService(db).list(page.offset, page.limit, department_id)
    return Page[EmployeeRead](
        data=[_to_read(i) for i in items],
        pagination=PageMeta(page=page.page, page_size=page.page_size, total=total),
    )


@router.post("", response_model=EmployeeRead, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)) -> EmployeeRead:
    return _to_read(EmployeeService(db).create(payload))


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: Session = Depends(get_db)) -> EmployeeRead:
    return _to_read(EmployeeService(db).get(employee_id))


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)
) -> EmployeeRead:
    return _to_read(EmployeeService(db).update(employee_id, payload))


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: Session = Depends(get_db)) -> None:
    EmployeeService(db).delete(employee_id)
