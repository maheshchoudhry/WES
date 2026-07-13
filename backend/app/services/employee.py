"""Employee service — registration, department assignment, and business rules."""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.employee import Employee
from app.repositories.company import CompanyRepository
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    def __init__(self, db: Session):
        self.db = db
        self.employees = EmployeeRepository(db)
        self.companies = CompanyRepository(db)
        self.departments = DepartmentRepository(db)

    def get(self, employee_id: uuid.UUID) -> Employee:
        employee = self.employees.get(employee_id)
        if employee is None:
            raise NotFoundError(f"Employee {employee_id} not found")
        return employee

    def list(
        self,
        *,
        company_id: uuid.UUID | None = None,
        department_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Employee], int]:
        items = self.employees.list_filtered(
            company_id=company_id, department_id=department_id, offset=offset, limit=limit
        )
        # Count reflects the same filters when scoped to a department; otherwise total.
        if department_id is not None:
            total = self.employees.count_by_department(department_id)
        else:
            total = self.employees.count()
        return items, total

    def _validate_department_in_company(
        self, company_id: uuid.UUID, department_id: uuid.UUID
    ) -> None:
        department = self.departments.get(department_id)
        if department is None:
            raise ValidationError(f"Department {department_id} does not exist")
        if department.company_id != company_id:
            raise ValidationError("Department does not belong to the employee's company")

    def register(self, payload: EmployeeCreate) -> Employee:
        """Register a new employee (registration + optional department assignment)."""
        # Business rule: employee must belong to an existing company.
        if self.companies.get(payload.company_id) is None:
            raise ValidationError(f"Company {payload.company_id} does not exist")
        # Business rule: unique employee_code and email.
        if self.employees.get_by_code(payload.employee_code):
            raise ConflictError(f"Employee code '{payload.employee_code}' already exists")
        if self.employees.get_by_email(payload.email):
            raise ConflictError(f"Employee email '{payload.email}' already exists")
        # Business rule: assigned department must belong to the same company.
        if payload.department_id is not None:
            self._validate_department_in_company(payload.company_id, payload.department_id)
        # Business rule: a referenced manager must exist.
        if payload.reports_to_id is not None and self.employees.get(payload.reports_to_id) is None:
            raise ValidationError(f"Manager {payload.reports_to_id} does not exist")

        data = payload.model_dump()
        data["email"] = str(data["email"])
        employee = Employee(**data)
        return self.employees.add(employee)

    def update(self, employee_id: uuid.UUID, payload: EmployeeUpdate) -> Employee:
        employee = self.get(employee_id)
        data = payload.model_dump(exclude_unset=True)
        if "email" in data and data["email"] is not None:
            data["email"] = str(data["email"])
            existing = self.employees.get_by_email(data["email"])
            if existing and existing.id != employee.id:
                raise ConflictError(f"Employee email '{data['email']}' already exists")
        if "reports_to_id" in data and data["reports_to_id"] is not None:
            if data["reports_to_id"] == employee.id:
                raise ValidationError("An employee cannot report to themselves")
            if self.employees.get(data["reports_to_id"]) is None:
                raise ValidationError(f"Manager {data['reports_to_id']} does not exist")
        for field, value in data.items():
            setattr(employee, field, value)
        self.db.flush()
        self.db.refresh(employee)
        return employee

    def assign_department(
        self, employee_id: uuid.UUID, department_id: uuid.UUID | None
    ) -> Employee:
        """Assign the employee to a department (or clear it when ``None``)."""
        employee = self.get(employee_id)
        if department_id is not None:
            self._validate_department_in_company(employee.company_id, department_id)
        employee.department_id = department_id
        self.db.flush()
        self.db.refresh(employee)
        return employee

    def delete(self, employee_id: uuid.UUID) -> None:
        employee = self.get(employee_id)
        self.employees.delete(employee)
