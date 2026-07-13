"""Shared API dependencies (pagination + service providers)."""

from dataclasses import dataclass

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.company import CompanyService
from app.services.department import DepartmentService
from app.services.employee import EmployeeService


@dataclass
class Pagination:
    offset: int
    limit: int


def pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Pagination:
    return Pagination(offset=(page - 1) * page_size, limit=page_size)


def get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    return CompanyService(db)


def get_department_service(db: Session = Depends(get_db)) -> DepartmentService:
    return DepartmentService(db)


def get_employee_service(db: Session = Depends(get_db)) -> EmployeeService:
    return EmployeeService(db)
