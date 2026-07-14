"""enterprise devops, ci/cd & production platform schema

Creates environment_profiles, deployment_targets, pipeline_runs, build_runs,
release_versions, release_notes, deployment_artifacts, deployment_runs,
rollback_history, monitoring_events, system_health, and incident_reports.

Revision ID: 0012_enterprise_devops
Revises: 0011_quality_gate_engine
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0012_enterprise_devops"
down_revision: Union[str, None] = "0011_quality_gate_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return (
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def _created():
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "environment_profiles",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("strategy", sa.String(length=20), nullable=False, server_default="standard"),
        sa.Column("variables", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_environment_profiles_name"),
    )
    op.create_index("ix_environment_profiles_name", "environment_profiles", ["name"])

    op.create_table(
        "deployment_targets",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("strategy", sa.String(length=20), nullable=False, server_default="standard"),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deployment_targets_environment", "deployment_targets", ["environment"])

    op.create_table(
        "release_versions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("task_id", GUID(), nullable=True),
        sa.Column("pipeline_run_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="beta"),
        sa.Column("created_by", sa.String(length=200), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", name="uq_release_versions_version"),
    )
    op.create_index("ix_release_versions_version", "release_versions", ["version"])

    op.create_table(
        "pipeline_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("task_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("environment_target", sa.String(length=40), nullable=False, server_default="staging"),
        sa.Column("current_stage", sa.String(length=40), nullable=True),
        sa.Column("stages", sa.Text(), nullable=True),
        sa.Column("triggered_by", sa.String(length=200), nullable=True),
        sa.Column("release_version_id", GUID(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["release_version_id"], ["release_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_pipeline_runs_code"),
    )
    op.create_index("ix_pipeline_runs_code", "pipeline_runs", ["code"])
    op.create_index("ix_pipeline_runs_task_id", "pipeline_runs", ["task_id"])
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"])

    op.create_table(
        "build_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=True),
        sa.Column("pipeline_run_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("language", sa.String(length=40), nullable=True),
        sa.Column("commands", sa.Text(), nullable=True),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("checksum", sa.String(length=80), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["pipeline_run_id"], ["pipeline_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_build_runs_pipeline_run_id", "build_runs", ["pipeline_run_id"])

    op.create_table(
        "release_notes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("release_version_id", GUID(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("changes", sa.Text(), nullable=True),
        sa.Column("highlights", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["release_version_id"], ["release_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_release_notes_release_version_id", "release_notes", ["release_version_id"])

    op.create_table(
        "deployment_artifacts",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("release_version_id", GUID(), nullable=True),
        sa.Column("build_run_id", GUID(), nullable=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="tarball"),
        sa.Column("path", sa.String(length=1000), nullable=True),
        sa.Column("checksum", sa.String(length=80), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("image_tag", sa.String(length=200), nullable=True),
        sa.Column("artifact_metadata", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["release_version_id"], ["release_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["build_run_id"], ["build_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deployment_artifacts_release_version_id", "deployment_artifacts", ["release_version_id"]
    )

    op.create_table(
        "deployment_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("pipeline_run_id", GUID(), nullable=True),
        sa.Column("task_id", GUID(), nullable=True),
        sa.Column("release_version_id", GUID(), nullable=True),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("target_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("strategy", sa.String(length=20), nullable=False, server_default="standard"),
        sa.Column("path", sa.String(length=1000), nullable=True),
        sa.Column("approved_by", sa.String(length=200), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["pipeline_run_id"], ["pipeline_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["release_version_id"], ["release_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_id"], ["deployment_targets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deployment_runs_pipeline_run_id", "deployment_runs", ["pipeline_run_id"])
    op.create_index("ix_deployment_runs_environment", "deployment_runs", ["environment"])

    op.create_table(
        "rollback_history",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("deployment_run_id", GUID(), nullable=True),
        sa.Column("from_release_id", GUID(), nullable=True),
        sa.Column("to_release_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("actor", sa.String(length=200), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["deployment_run_id"], ["deployment_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_release_id"], ["release_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_release_id"], ["release_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rollback_history_environment", "rollback_history", ["environment"])

    op.create_table(
        "monitoring_events",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("metric", sa.String(length=60), nullable=False),
        sa.Column("value", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="healthy"),
        sa.Column("detail", sa.Text(), nullable=True),
        _created(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_events_category", "monitoring_events", ["category"])

    op.create_table(
        "system_health",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("overall_status", sa.String(length=20), nullable=False),
        sa.Column("app_status", sa.String(length=20), nullable=False, server_default="healthy"),
        sa.Column("api_status", sa.String(length=20), nullable=False, server_default="healthy"),
        sa.Column("db_status", sa.String(length=20), nullable=False, server_default="healthy"),
        sa.Column("provider_status", sa.String(length=20), nullable=False, server_default="healthy"),
        sa.Column("cpu_pct", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("memory_pct", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("disk_pct", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("queue_depth", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("response_time_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        _created(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "incident_reports",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="warning"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("source", sa.String(length=60), nullable=False, server_default="monitoring"),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("recovery_action", sa.Text(), nullable=True),
        sa.Column("deployment_run_id", GUID(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["deployment_run_id"], ["deployment_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_incident_reports_code"),
    )
    op.create_index("ix_incident_reports_code", "incident_reports", ["code"])
    op.create_index("ix_incident_reports_severity", "incident_reports", ["severity"])


def downgrade() -> None:
    for tbl in (
        "incident_reports",
        "system_health",
        "monitoring_events",
        "rollback_history",
        "deployment_runs",
        "deployment_artifacts",
        "release_notes",
        "build_runs",
        "pipeline_runs",
        "release_versions",
        "deployment_targets",
        "environment_profiles",
    ):
        op.drop_table(tbl)
