"""Repositories for the AI Company Core."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.ai import AICapability, AIDepartment, AIEmployee, AIRole
from app.repositories.base import BaseRepository


class AIDepartmentRepository(BaseRepository[AIDepartment]):
    model = AIDepartment

    def list_all(self) -> list[AIDepartment]:
        return list(self.db.scalars(select(AIDepartment).order_by(AIDepartment.code)).all())

    def get_by_code(self, code: str) -> AIDepartment | None:
        return self.db.scalar(select(AIDepartment).where(AIDepartment.code == code))


class AIRoleRepository(BaseRepository[AIRole]):
    model = AIRole

    def list_all(self) -> list[AIRole]:
        return list(self.db.scalars(select(AIRole).order_by(AIRole.code)).all())

    def get_by_code(self, code: str) -> AIRole | None:
        return self.db.scalar(select(AIRole).where(AIRole.code == code))


class AICapabilityRepository(BaseRepository[AICapability]):
    model = AICapability

    def list_all(self) -> list[AICapability]:
        return list(self.db.scalars(select(AICapability).order_by(AICapability.code)).all())

    def get_by_codes(self, codes: list[str]) -> list[AICapability]:
        if not codes:
            return []
        return list(self.db.scalars(select(AICapability).where(AICapability.code.in_(codes))).all())


class AIEmployeeRepository(BaseRepository[AIEmployee]):
    model = AIEmployee

    _EAGER = (
        selectinload(AIEmployee.department),
        selectinload(AIEmployee.role),
        selectinload(AIEmployee.manager),
        selectinload(AIEmployee.responsibilities),
        selectinload(AIEmployee.kpis),
        selectinload(AIEmployee.capabilities),
    )

    def get(self, entity_id: uuid.UUID, *, include_deleted: bool = False) -> AIEmployee | None:
        stmt = select(AIEmployee).where(AIEmployee.id == entity_id).options(*self._EAGER)
        if not include_deleted:
            stmt = stmt.where(AIEmployee.is_deleted.is_(False))
        return self.db.scalar(stmt)

    def get_by_code(self, code: str, *, include_deleted: bool = True) -> AIEmployee | None:
        stmt = select(AIEmployee).where(AIEmployee.employee_code == code)
        if not include_deleted:
            stmt = stmt.where(AIEmployee.is_deleted.is_(False))
        return self.db.scalar(stmt)

    def _filtered_stmt(
        self,
        *,
        department_id: uuid.UUID | None,
        role_id: uuid.UUID | None,
        status: str | None,
        search: str | None,
    ):
        stmt = select(AIEmployee).where(AIEmployee.is_deleted.is_(False))
        if department_id is not None:
            stmt = stmt.where(AIEmployee.department_id == department_id)
        if role_id is not None:
            stmt = stmt.where(AIEmployee.role_id == role_id)
        if status is not None:
            stmt = stmt.where(AIEmployee.status == status)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(AIEmployee.name).like(like),
                    func.lower(AIEmployee.employee_code).like(like),
                )
            )
        return stmt

    def list_filtered(
        self,
        *,
        department_id: uuid.UUID | None = None,
        role_id: uuid.UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AIEmployee]:
        stmt = (
            self._filtered_stmt(
                department_id=department_id, role_id=role_id, status=status, search=search
            )
            .options(*self._EAGER)
            .order_by(AIEmployee.employee_code)
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_filtered(
        self,
        *,
        department_id: uuid.UUID | None = None,
        role_id: uuid.UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        base = self._filtered_stmt(
            department_id=department_id, role_id=role_id, status=status, search=search
        ).subquery()
        return int(self.db.scalar(select(func.count()).select_from(base)) or 0)

    def list_active(self) -> list[AIEmployee]:
        stmt = (
            select(AIEmployee)
            .where(AIEmployee.is_deleted.is_(False))
            .options(*self._EAGER)
            .order_by(AIEmployee.employee_code)
        )
        return list(self.db.scalars(stmt).all())

    def count_active(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(AIEmployee).where(AIEmployee.is_deleted.is_(False))
            )
            or 0
        )

    def count_direct_reports(self, manager_id: uuid.UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(AIEmployee)
                .where(
                    AIEmployee.manager_id == manager_id,
                    AIEmployee.is_deleted.is_(False),
                )
            )
            or 0
        )
