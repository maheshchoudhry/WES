"""Department service — business rules for the Department domain."""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.department import Department
from app.repositories.company import CompanyRepository
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    def __init__(self, db: Session):
        self.db = db
        self.departments = DepartmentRepository(db)
        self.companies = CompanyRepository(db)
        self.employees = EmployeeRepository(db)

    def get(self, department_id: uuid.UUID) -> Department:
        department = self.departments.get(department_id)
        if department is None:
            raise NotFoundError(f"Department {department_id} not found")
        return department

    def list(
        self, *, company_id: uuid.UUID | None = None, offset: int = 0, limit: int = 100
    ) -> tuple[list[Department], int]:
        if company_id is not None:
            items = self.departments.list_by_company(company_id, offset=offset, limit=limit)
            return items, self.departments.count_by_company(company_id)
        return self.departments.list(offset=offset, limit=limit), self.departments.count()

    def create(self, payload: DepartmentCreate) -> Department:
        # Business rule: department must belong to an existing company.
        if self.companies.get(payload.company_id) is None:
            raise ValidationError(f"Company {payload.company_id} does not exist")
        # Business rule: code and name are unique within the company.
        if self.departments.get_by_code(payload.company_id, payload.code):
            raise ConflictError(f"Department code '{payload.code}' already exists in this company")
        if self.departments.get_by_name(payload.company_id, payload.name):
            raise ConflictError(f"Department name '{payload.name}' already exists in this company")
        department = Department(**payload.model_dump())
        return self.departments.add(department)

    def update(self, department_id: uuid.UUID, payload: DepartmentUpdate) -> Department:
        department = self.get(department_id)
        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"] != department.code:
            if self.departments.get_by_code(department.company_id, data["code"]):
                raise ConflictError(
                    f"Department code '{data['code']}' already exists in this company"
                )
        if "name" in data and data["name"] != department.name:
            if self.departments.get_by_name(department.company_id, data["name"]):
                raise ConflictError(
                    f"Department name '{data['name']}' already exists in this company"
                )
        for field, value in data.items():
            setattr(department, field, value)
        self.db.flush()
        self.db.refresh(department)
        return department

    def delete(self, department_id: uuid.UUID) -> None:
        department = self.get(department_id)
        # Business rule: cannot delete a department that still has employees.
        if self.employees.count_by_department(department.id) > 0:
            raise ConflictError("Department has assigned employees; reassign them before deleting")
        self.departments.delete(department)
