"""Department repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db: Session) -> None:
        super().__init__(Department, db)

    def get_by_code(self, code: str) -> Department | None:
        return self.db.scalar(select(Department).where(Department.code == code))
