"""Provider Platform ORM models (Sprint 11).

Extends the orchestration layer for live provider integration: encrypted
credentials, selectable models, rich usage/billing/latency/error/event tracking,
and founder budget configuration. Secrets are stored as ciphertext only — see
``app.core.secrets``.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProviderSecret(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An encrypted provider credential, scoped to an environment profile."""

    __tablename__ = "provider_secrets"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="development")
    key_name: Mapped[str] = mapped_column(String(60), nullable=False, default="api_key")
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[str | None] = mapped_column(String(60), nullable=True)
    last_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProviderModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A selectable model offered by a provider, with per-model pricing."""

    __tablename__ = "provider_models"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    context_window: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_cost_per_1k: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    output_cost_per_1k: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class ProviderUsage(UUIDPrimaryKeyMixin, Base):
    """Per-execution usage, dimensioned for per provider/employee/project/day/month rollups."""

    __tablename__ = "provider_usage"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("execution_runs.id", ondelete="SET NULL"), nullable=True
    )
    ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    actual_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    day: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # YYYY-MM
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProviderBilling(UUIDPrimaryKeyMixin, Base):
    """Aggregated spend per provider per period (day/month)."""

    __tablename__ = "provider_billing"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(10), nullable=False)  # day | month
    period_key: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ProviderLatency(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "provider_latency"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("execution_runs.id", ondelete="SET NULL"), nullable=True
    )
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProviderErrorLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "provider_errors"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("execution_runs.id", ondelete="SET NULL"), nullable=True
    )
    error_type: Mapped[str] = mapped_column(String(40), nullable=False, default="error")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProviderEvent(UUIDPrimaryKeyMixin, Base):
    """Audit + notification log for provider configuration and failover events."""

    __tablename__ = "provider_events"

    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_providers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BudgetConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Founder-configured spend/token guardrails (single global scope by default)."""

    __tablename__ = "budget_configs"

    scope: Mapped[str] = mapped_column(String(40), nullable=False, default="global", unique=True)
    daily_cost_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    monthly_cost_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warning_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    hard_stop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
