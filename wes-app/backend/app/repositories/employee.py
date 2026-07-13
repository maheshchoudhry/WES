"""Employee repository."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    def __init__(self, db: Session) -> None:
        super().__init__(Employee, db)

    def get_by_code(self, code: str) -> Employee | None:
        return self.db.scalar(select(Employee).where(Employee.employee_code == code))

    def list(
        self, offset: int = 0, limit: int = 50, department_id: int | None = None
    ) -> list[Employee]:
        stmt = select(Employee).order_by(Employee.id)
        if department_id is not None:
            stmt = stmt.where(Employee.department_id == department_id)
        return list(self.db.scalars(stmt.offset(offset).limit(limit)))

    def count(self, department_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Employee)
        if department_id is not None:
            stmt = stmt.where(Employee.department_id == department_id)
        return self.db.scalar(stmt) or 0
