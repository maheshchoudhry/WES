"""Department repository."""

import uuid

from sqlalchemy import func, select

from app.models.department import Department
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    model = Department

    def list_by_company(
        self, company_id: uuid.UUID, *, offset: int = 0, limit: int = 100
    ) -> list[Department]:
        stmt = (
            select(Department)
            .where(Department.company_id == company_id)
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_code(self, company_id: uuid.UUID, code: str) -> Department | None:
        return self.db.scalar(
            select(Department).where(
                Department.company_id == company_id, Department.code == code
            )
        )

    def get_by_name(self, company_id: uuid.UUID, name: str) -> Department | None:
        return self.db.scalar(
            select(Department).where(
                Department.company_id == company_id, Department.name == name
            )
        )

    def count_by_company(self, company_id: uuid.UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Department)
                .where(Department.company_id == company_id)
            )
            or 0
        )
