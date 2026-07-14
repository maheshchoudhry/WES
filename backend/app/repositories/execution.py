"""Repositories for the AI Execution Engine."""

import uuid

from sqlalchemy import func, select

from app.models.execution import (
    SOP,
    AIWorkspace,
    DecisionRule,
    ExecutionContext,
    ExecutionHistory,
    ExecutionQueueItem,
    Handoff,
    PromptTemplate,
    ReviewItem,
)
from app.repositories.base import BaseRepository


class PromptRepository(BaseRepository[PromptTemplate]):
    model = PromptTemplate

    def list_all(self) -> list[PromptTemplate]:
        return list(self.db.scalars(select(PromptTemplate).order_by(PromptTemplate.code)).all())

    def get_by_code(self, code: str) -> PromptTemplate | None:
        return self.db.scalar(select(PromptTemplate).where(PromptTemplate.code == code))


class SOPRepository(BaseRepository[SOP]):
    model = SOP

    def list_all(self) -> list[SOP]:
        return list(self.db.scalars(select(SOP).order_by(SOP.code)).all())

    def get_by_code(self, code: str) -> SOP | None:
        return self.db.scalar(select(SOP).where(SOP.code == code))


class DecisionRuleRepository(BaseRepository[DecisionRule]):
    model = DecisionRule

    def list_all(self) -> list[DecisionRule]:
        return list(self.db.scalars(select(DecisionRule)).all())

    def list_by_role(self, role_id: uuid.UUID) -> list[DecisionRule]:
        return list(
            self.db.scalars(select(DecisionRule).where(DecisionRule.ai_role_id == role_id)).all()
        )


class WorkspaceRepository(BaseRepository[AIWorkspace]):
    model = AIWorkspace

    def get_by_employee(self, employee_id: uuid.UUID) -> AIWorkspace | None:
        return self.db.scalar(select(AIWorkspace).where(AIWorkspace.ai_employee_id == employee_id))


class QueueRepository(BaseRepository[ExecutionQueueItem]):
    model = ExecutionQueueItem

    def list_all(self) -> list[ExecutionQueueItem]:
        return list(
            self.db.scalars(
                select(ExecutionQueueItem).order_by(
                    ExecutionQueueItem.position, ExecutionQueueItem.created_at
                )
            ).all()
        )

    def list_filtered(self, *, ai_employee_id=None, status=None) -> list[ExecutionQueueItem]:
        stmt = select(ExecutionQueueItem)
        if ai_employee_id is not None:
            stmt = stmt.where(ExecutionQueueItem.ai_employee_id == ai_employee_id)
        if status is not None:
            stmt = stmt.where(ExecutionQueueItem.status == status)
        stmt = stmt.order_by(ExecutionQueueItem.position, ExecutionQueueItem.created_at)
        return list(self.db.scalars(stmt).all())


class HistoryRepository(BaseRepository[ExecutionHistory]):
    model = ExecutionHistory

    def list_all(self) -> list[ExecutionHistory]:
        return list(
            self.db.scalars(
                select(ExecutionHistory).order_by(ExecutionHistory.created_at.desc())
            ).all()
        )

    def list_by_employee(self, employee_id: uuid.UUID) -> list[ExecutionHistory]:
        return list(
            self.db.scalars(
                select(ExecutionHistory)
                .where(ExecutionHistory.ai_employee_id == employee_id)
                .order_by(ExecutionHistory.created_at.desc())
            ).all()
        )


class ReviewRepository(BaseRepository[ReviewItem]):
    model = ReviewItem

    def list_filtered(self, *, reviewer_id=None, status=None) -> list[ReviewItem]:
        stmt = select(ReviewItem)
        if reviewer_id is not None:
            stmt = stmt.where(ReviewItem.reviewer_ai_employee_id == reviewer_id)
        if status is not None:
            stmt = stmt.where(ReviewItem.status == status)
        stmt = stmt.order_by(ReviewItem.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def list_all(self) -> list[ReviewItem]:
        return list(self.db.scalars(select(ReviewItem)).all())


class HandoffRepository(BaseRepository[Handoff]):
    model = Handoff

    def list_all(self) -> list[Handoff]:
        return list(self.db.scalars(select(Handoff).order_by(Handoff.sequence)).all())

    def list_by_work_item(self, work_item_id: uuid.UUID) -> list[Handoff]:
        return list(
            self.db.scalars(
                select(Handoff)
                .where(Handoff.work_item_id == work_item_id)
                .order_by(Handoff.sequence)
            ).all()
        )

    def list_pending_for(self, employee_id: uuid.UUID) -> list[Handoff]:
        from app.domain.execution_enums import HandoffStatus

        return list(
            self.db.scalars(
                select(Handoff)
                .where(
                    Handoff.to_ai_employee_id == employee_id,
                    Handoff.status != HandoffStatus.COMPLETED,
                )
                .order_by(Handoff.sequence)
            ).all()
        )


class ContextRepository(BaseRepository[ExecutionContext]):
    model = ExecutionContext

    def list_by_employee(self, employee_id: uuid.UUID) -> list[ExecutionContext]:
        return list(
            self.db.scalars(
                select(ExecutionContext).where(ExecutionContext.ai_employee_id == employee_id)
            ).all()
        )


def count_by(db, model, column, value) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(column == value)) or 0)
