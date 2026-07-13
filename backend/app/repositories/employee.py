"""Employee repository."""

import uuid

from sqlalchemy import func, select

from app.models.employee import Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    def get_by_code(self, employee_code: str) -> Employee | None:
        return self.db.scalar(select(Employee).where(Employee.employee_code == employee_code))

    def get_by_email(self, email: str) -> Employee | None:
        return self.db.scalar(select(Employee).where(Employee.email == email))

    def list_filtered(
        self,
        *,
        company_id: uuid.UUID | None = None,
        department_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Employee]:
        stmt = select(Employee)
        if company_id is not None:
            stmt = stmt.where(Employee.company_id == company_id)
        if department_id is not None:
            stmt = stmt.where(Employee.department_id == department_id)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_by_department(self, department_id: uuid.UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Employee)
                .where(Employee.department_id == department_id)
            )
            or 0
        )
