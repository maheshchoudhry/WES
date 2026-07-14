"""ai review, security & quality gate engine schema

Creates quality_rules, quality_gate_runs, review_findings, security_findings,
performance_findings, dependency_findings, documentation_findings,
compliance_findings, quality_metrics, and release_readiness.

Revision ID: 0011_quality_gate_engine
Revises: 0010_autonomous_development
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0011_quality_gate_engine"
down_revision: Union[str, None] = "0010_autonomous_development"
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


def _finding_cols():
    return (
        sa.Column("id", GUID(), nullable=False),
        sa.Column("gate_run_id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
    )


def _finding_fks():
    return (
        sa.ForeignKeyConstraint(["gate_run_id"], ["quality_gate_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def upgrade() -> None:
    op.create_table(
        "quality_rules",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("operator", sa.String(length=10), nullable=False, server_default="gte"),
        sa.Column("threshold", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="high"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("mandatory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("description", sa.Text(), nullable=True),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_quality_rules_code"),
    )
    op.create_index("ix_quality_rules_code", "quality_rules", ["code"])

    op.create_table(
        "quality_gate_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="running"),
        sa.Column("architecture_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("code_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("security_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("performance_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("documentation_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("tests_passed_pct", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("formatting_clean", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("lint_clean", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("documentation_complete", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("high_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_findings", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("approval_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("gates", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quality_gate_runs_task_id", "quality_gate_runs", ["task_id"])

    op.create_table(
        "review_findings",
        *_finding_cols(),
        sa.Column("engine", sa.String(length=30), nullable=False, server_default="architecture"),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
        *_finding_fks(),
    )
    op.create_index("ix_review_findings_gate_run_id", "review_findings", ["gate_run_id"])
    op.create_index("ix_review_findings_task_id", "review_findings", ["task_id"])

    op.create_table(
        "security_findings",
        *_finding_cols(),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
        sa.Column("cwe", sa.String(length=20), nullable=True),
        *_finding_fks(),
    )
    op.create_index("ix_security_findings_gate_run_id", "security_findings", ["gate_run_id"])
    op.create_index("ix_security_findings_task_id", "security_findings", ["task_id"])

    op.create_table(
        "performance_findings",
        *_finding_cols(),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
        *_finding_fks(),
    )
    op.create_index("ix_performance_findings_gate_run_id", "performance_findings", ["gate_run_id"])
    op.create_index("ix_performance_findings_task_id", "performance_findings", ["task_id"])

    op.create_table(
        "dependency_findings",
        *_finding_cols(),
        sa.Column("package", sa.String(length=200), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=False),
        *_finding_fks(),
    )
    op.create_index("ix_dependency_findings_gate_run_id", "dependency_findings", ["gate_run_id"])
    op.create_index("ix_dependency_findings_task_id", "dependency_findings", ["task_id"])

    op.create_table(
        "documentation_findings",
        *_finding_cols(),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        *_finding_fks(),
    )
    op.create_index(
        "ix_documentation_findings_gate_run_id", "documentation_findings", ["gate_run_id"]
    )
    op.create_index("ix_documentation_findings_task_id", "documentation_findings", ["task_id"])

    op.create_table(
        "compliance_findings",
        *_finding_cols(),
        sa.Column("policy", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        *_finding_fks(),
    )
    op.create_index("ix_compliance_findings_gate_run_id", "compliance_findings", ["gate_run_id"])
    op.create_index("ix_compliance_findings_task_id", "compliance_findings", ["task_id"])

    op.create_table(
        "quality_metrics",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("gate_run_id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("impact_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("complexity_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("maintainability_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        _created(),
        sa.ForeignKeyConstraint(["gate_run_id"], ["quality_gate_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quality_metrics_gate_run_id", "quality_metrics", ["gate_run_id"])
    op.create_index("ix_quality_metrics_task_id", "quality_metrics", ["task_id"])

    op.create_table(
        "release_readiness",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("gate_run_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("ready", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("blockers", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["gate_run_id"], ["quality_gate_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_release_readiness_task_id", "release_readiness", ["task_id"])


def downgrade() -> None:
    for tbl in (
        "release_readiness",
        "quality_metrics",
        "compliance_findings",
        "documentation_findings",
        "dependency_findings",
        "performance_findings",
        "security_findings",
        "review_findings",
        "quality_gate_runs",
        "quality_rules",
    ):
        op.drop_table(tbl)
