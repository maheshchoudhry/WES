"""AI Orchestration Engine ORM models (Sprint 09).

Provider registry/config, execution runs and messages, conversation threads,
metrics, token usage, cost tracking, provider health, and retry history. Fully
provider-independent — no provider-specific columns.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.orchestration_enums import (
    MessageRole,
    ProviderHealthStatus,
    ReviewOutcome,
    RunStatus,
)
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIProvider(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_providers"

    name: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Live-provider platform (Sprint 11): the currently-selected model and the
    # failover priority (lower runs first when the default provider fails).
    active_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)


class ProviderConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_configs"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)


class ConversationThread(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversation_threads"

    ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class ExecutionRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "execution_runs"

    thread_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("conversation_threads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[RunStatus] = mapped_column(
        String(20), nullable=False, default=RunStatus.QUEUED, index=True
    )
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_outcome: Mapped[ReviewOutcome | None] = mapped_column(String(20), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ExecutionMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "execution_messages"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("conversation_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("execution_runs.id", ondelete="SET NULL"), nullable=True
    )
    role: Mapped[MessageRole] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ExecutionMetric(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "execution_metrics"

    run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("execution_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TokenUsage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "token_usage"

    run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("execution_runs.id", ondelete="SET NULL"), nullable=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CostTracking(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "cost_tracking"

    run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("execution_runs.id", ondelete="SET NULL"), nullable=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProviderHealthRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "provider_health"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ProviderHealthStatus] = mapped_column(String(20), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RetryHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "retry_history"

    run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("execution_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
