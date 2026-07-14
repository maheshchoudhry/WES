"""Enterprise DevOps Platform ORM models (Sprint 15).

Completes the lifecycle: an approved, quality-gated implementation flows through a
CI/CD pipeline (build → test → security → docker → artifact → release → deploy),
into monitored, rollback-ready environments. All production deployment is
Founder-gated; nothing is pushed or deployed to a real production host.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.devops_enums import (
    BuildStatus,
    DeploymentStatus,
    DeployStrategy,
    HealthStatus,
    IncidentSeverity,
    IncidentStatus,
    PipelineStatus,
    ReleaseStatus,
    RollbackStatus,
)
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class EnvironmentProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "environment_profiles"

    name: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    strategy: Mapped[DeployStrategy] = mapped_column(
        String(20), nullable=False, default=DeployStrategy.STANDARD
    )
    variables: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON (non-secret)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class DeploymentTarget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deployment_targets"

    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    strategy: Mapped[DeployStrategy] = mapped_column(
        String(20), nullable=False, default=DeployStrategy.STANDARD
    )
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PipelineRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "pipeline_runs"

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[PipelineStatus] = mapped_column(
        String(30), nullable=False, default=PipelineStatus.QUEUED, index=True
    )
    environment_target: Mapped[str] = mapped_column(String(40), nullable=False, default="staging")
    current_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    stages: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON per-stage summary
    triggered_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    release_version_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("release_versions.id", ondelete="SET NULL"), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BuildRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "build_runs"

    task_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="SET NULL"), nullable=True
    )
    pipeline_run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=True, index=True
    )
    status: Mapped[BuildStatus] = mapped_column(
        String(20), nullable=False, default=BuildStatus.PENDING
    )
    language: Mapped[str | None] = mapped_column(String(40), nullable=True)
    commands: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(80), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReleaseVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "release_versions"

    version: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="SET NULL"), nullable=True
    )
    # Soft reference (no FK) to avoid a pipeline_runs<->release_versions cycle;
    # pipeline_runs.release_version_id holds the enforced foreign key.
    pipeline_run_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    status: Mapped[ReleaseStatus] = mapped_column(
        String(20), nullable=False, default=ReleaseStatus.DRAFT
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="beta")
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReleaseNote(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "release_notes"

    release_version_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("release_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    changes: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    highlights: Mapped[str | None] = mapped_column(Text, nullable=True)


class DeploymentArtifact(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "deployment_artifacts"

    release_version_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("release_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    build_run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("build_runs.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="tarball")
    path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(80), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_tag: Mapped[str | None] = mapped_column(String(200), nullable=True)
    artifact_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DeploymentRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "deployment_runs"

    pipeline_run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("pipeline_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="SET NULL"), nullable=True
    )
    release_version_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("release_versions.id", ondelete="SET NULL"), nullable=True
    )
    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("deployment_targets.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[DeploymentStatus] = mapped_column(
        String(20), nullable=False, default=DeploymentStatus.PENDING
    )
    strategy: Mapped[DeployStrategy] = mapped_column(
        String(20), nullable=False, default=DeployStrategy.STANDARD
    )
    path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RollbackHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "rollback_history"

    environment: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    deployment_run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("deployment_runs.id", ondelete="SET NULL"), nullable=True
    )
    from_release_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("release_versions.id", ondelete="SET NULL"), nullable=True
    )
    to_release_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("release_versions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[RollbackStatus] = mapped_column(
        String(20), nullable=False, default=RollbackStatus.PENDING
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MonitoringEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "monitoring_events"

    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(60), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[HealthStatus] = mapped_column(
        String(20), nullable=False, default=HealthStatus.HEALTHY
    )
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SystemHealth(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "system_health"

    overall_status: Mapped[HealthStatus] = mapped_column(String(20), nullable=False)
    app_status: Mapped[str] = mapped_column(String(20), nullable=False, default="healthy")
    api_status: Mapped[str] = mapped_column(String(20), nullable=False, default="healthy")
    db_status: Mapped[str] = mapped_column(String(20), nullable=False, default="healthy")
    provider_status: Mapped[str] = mapped_column(String(20), nullable=False, default="healthy")
    cpu_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    memory_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    disk_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    queue_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class IncidentReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "incident_reports"

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(
        String(20), nullable=False, default=IncidentSeverity.WARNING, index=True
    )
    status: Mapped[IncidentStatus] = mapped_column(
        String(20), nullable=False, default=IncidentStatus.OPEN
    )
    source: Mapped[str] = mapped_column(String(60), nullable=False, default="monitoring")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    recovery_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    deployment_run_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("deployment_runs.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
