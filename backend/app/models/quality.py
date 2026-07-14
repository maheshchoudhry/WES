"""AI Review, Security & Quality Gate Engine ORM models (Sprint 14).

The final engineering-validation layer. Each autonomous implementation is run
through architecture/code/security/performance/dependency/documentation review
engines, aggregated into a quality gate run with per-gate scores and findings,
scored for risk, checked for compliance, and assessed for release readiness — all
before it can reach Founder approval.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.quality_enums import (
    ComplianceStatus,
    FindingSeverity,
    GateStatus,
    ReadinessStatus,
)
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class QualityRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A configurable quality-gate threshold (e.g. architecture_score >= 90)."""

    __tablename__ = "quality_rules"

    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    operator: Mapped[str] = mapped_column(String(10), nullable=False, default="gte")  # gte|lte|eq
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    severity: Mapped[FindingSeverity] = mapped_column(
        String(20), nullable=False, default=FindingSeverity.HIGH
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class QualityGateRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "quality_gate_runs"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[GateStatus] = mapped_column(
        String(20), nullable=False, default=GateStatus.RUNNING
    )
    architecture_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    code_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    security_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    performance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    documentation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tests_passed_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    formatting_clean: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    lint_clean: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    documentation_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    critical_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_findings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approval_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gates: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: per-gate pass/fail
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReviewFinding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "review_findings"

    gate_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("quality_gate_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    engine: Mapped[str] = mapped_column(
        String(30), nullable=False, default="architecture"
    )  # architecture|code
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class SecurityFinding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "security_findings"

    gate_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("quality_gate_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cwe: Mapped[str | None] = mapped_column(String(20), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class PerformanceFinding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "performance_findings"

    gate_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("quality_gate_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class DependencyFinding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "dependency_findings"

    gate_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("quality_gate_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    package: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class DocumentationFinding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "documentation_findings"

    gate_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("quality_gate_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class ComplianceFinding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "compliance_findings"

    gate_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("quality_gate_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    policy: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[ComplianceStatus] = mapped_column(String(20), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(
        String(20), nullable=False, default=FindingSeverity.INFO
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)


class QualityMetrics(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "quality_metrics"

    gate_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("quality_gate_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    complexity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    maintainability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReleaseReadiness(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "release_readiness"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gate_run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("quality_gate_runs.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ReadinessStatus] = mapped_column(String(20), nullable=False)
    ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
