"""Employee business logic."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError


class EmployeeService:
    def __init__(self, db: Session) -> None:
        self.repo = EmployeeRepository(db)
        self.departments = DepartmentRepository(db)

    def _check_department(self, department_id: int | None) -> None:
        if department_id is not None and self.departments.get(department_id) is None:
            raise ServiceError("Department does not exist", {"departmentId": department_id})

    def list(
        self, offset: int, limit: int, department_id: int | None = None
    ) -> tuple[list[Employee], int]:
        return (
            self.repo.list(offset, limit, department_id),
            self.repo.count(department_id),
        )

    def get(self, employee_id: int) -> Employee:
        obj = self.repo.get(employee_id)
        if obj is None:
            raise NotFoundError("Employee not found", {"id": employee_id})
        return obj

    def create(self, data: EmployeeCreate) -> Employee:
        if self.repo.get_by_code(data.employee_code) is not None:
            raise ConflictError(
                "Employee code already exists", {"employeeCode": data.employee_code}
            )
        self._check_department(data.department_id)
        return self.repo.save(Employee(**data.model_dump()))

    def update(self, employee_id: int, data: EmployeeUpdate) -> Employee:
        obj = self.get(employee_id)
        payload = data.model_dump(exclude_unset=True)
        new_code = payload.get("employee_code")
        if new_code and new_code != obj.employee_code and self.repo.get_by_code(new_code):
            raise ConflictError("Employee code already exists", {"employeeCode": new_code})
        if "department_id" in payload:
            self._check_department(payload["department_id"])
        for key, value in payload.items():
            setattr(obj, key, value)
        return self.repo.save(obj)

    def delete(self, employee_id: int) -> None:
        self.repo.delete(self.get(employee_id))
