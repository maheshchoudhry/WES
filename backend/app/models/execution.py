"""AI Execution Engine ORM models (Sprint 08).

Executable workspaces for AI employees: workspaces, execution queue, prompt and
SOP libraries, decision rules, execution history, review queue, handoffs, and
execution context. No LLM/AI execution — the operational framework only.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.execution_enums import (
    DecisionRuleType,
    ExecutionStatus,
    HandoffStatus,
    PromptType,
    ReviewStatus,
    SOPCategory,
)
from app.domain.work_enums import Priority
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIWorkspace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_workspaces"

    ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class PromptTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompt_templates"

    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt_type: Mapped[PromptType] = mapped_column(
        String(20), nullable=False, default=PromptType.TASK
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    author: Mapped[str | None] = mapped_column(String(160), nullable=True)


class SOP(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sop_library"

    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[SOPCategory] = mapped_column(
        String(20), nullable=False, default=SOPCategory.CODING
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class DecisionRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "decision_rules"

    ai_role_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_type: Mapped[DecisionRuleType] = mapped_column(
        String(20), nullable=False, default=DecisionRuleType.APPROVAL
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    authority_limit: Mapped[str | None] = mapped_column(String(160), nullable=True)


class ExecutionQueueItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "execution_queue"

    ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[Priority] = mapped_column(String(20), nullable=False, default=Priority.MEDIUM)
    status: Mapped[ExecutionStatus] = mapped_column(
        String(20), nullable=False, default=ExecutionStatus.QUEUED, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sop_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("sop_library.id", ondelete="SET NULL"), nullable=True
    )
    prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("prompt_templates.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExecutionHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "execution_history"

    ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True
    )
    execution_queue_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("execution_queue.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(160), nullable=False)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ExecutionStatus] = mapped_column(
        String(20), nullable=False, default=ExecutionStatus.COMPLETED
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReviewItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_queue"

    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    execution_history_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("execution_history.id", ondelete="SET NULL"), nullable=True
    )
    reviewer_ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submitter_ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ReviewStatus] = mapped_column(
        String(20), nullable=False, default=ReviewStatus.PENDING, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Handoff(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "handoffs"

    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    from_ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    to_ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[HandoffStatus] = mapped_column(
        String(20), nullable=False, default=HandoffStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExecutionContext(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "execution_context"

    ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True
    )
    key: Mapped[str] = mapped_column(String(160), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
