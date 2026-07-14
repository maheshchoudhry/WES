"""autonomous software development engine schema

Creates development_tasks, development_sessions, implementation_plans,
generated_changes, code_reviews, review_comments, test_runs, pull_requests,
approval_history, and implementation_metrics.

Revision ID: 0010_autonomous_development
Revises: 0009_repository_intelligence
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0010_autonomous_development"
down_revision: Union[str, None] = "0009_repository_intelligence"
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
        "development_tasks",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("work_item_id", GUID(), nullable=True),
        sa.Column("repository_id", GUID(), nullable=True),
        sa.Column("ai_employee_id", GUID(), nullable=True),
        sa.Column("sandbox_path", sa.String(length=1000), nullable=True),
        sa.Column("branch_name", sa.String(length=200), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_development_tasks_code"),
    )
    op.create_index("ix_development_tasks_code", "development_tasks", ["code"])
    op.create_index("ix_development_tasks_status", "development_tasks", ["status"])

    op.create_table(
        "development_sessions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("stage", sa.String(length=30), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_development_sessions_task_id", "development_sessions", ["task_id"])

    op.create_table(
        "implementation_plans",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("affected_files", sa.Text(), nullable=True),
        sa.Column("architecture_context", sa.Text(), nullable=True),
        sa.Column("dependencies", sa.Text(), nullable=True),
        sa.Column("required_knowledge", sa.Text(), nullable=True),
        sa.Column("required_apis", sa.Text(), nullable=True),
        sa.Column("implementation_order", sa.Text(), nullable=True),
        sa.Column("risk_analysis", sa.Text(), nullable=True),
        sa.Column("acceptance_criteria", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_implementation_plans_task_id", "implementation_plans", ["task_id"])

    op.create_table(
        "generated_changes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("path", sa.String(length=1000), nullable=False),
        sa.Column("old_path", sa.String(length=1000), nullable=True),
        sa.Column("change_type", sa.String(length=20), nullable=False),
        sa.Column("language", sa.String(length=40), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("diff", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="proposed"),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_changes_task_id", "generated_changes", ["task_id"])

    op.create_table(
        "code_reviews",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("summary", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_code_reviews_task_id", "code_reviews", ["task_id"])

    op.create_table(
        "review_comments",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("review_id", GUID(), nullable=False),
        sa.Column("dimension", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["code_reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_comments_review_id", "review_comments", ["review_id"])

    op.create_table(
        "test_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("command", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("passed_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_test_runs_task_id", "test_runs", ["task_id"])

    op.create_table(
        "pull_requests",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("branch_name", sa.String(length=200), nullable=False),
        sa.Column("base_branch", sa.String(length=200), nullable=False, server_default="main"),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("diff_summary", sa.Text(), nullable=True),
        sa.Column("release_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("commit_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("files_changed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("additions", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("deletions", sa.Integer(), nullable=False, server_default=sa.text("0")),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pull_requests_task_id", "pull_requests", ["task_id"])

    op.create_table(
        "approval_history",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("pull_request_id", GUID(), nullable=True),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("actor", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pull_request_id"], ["pull_requests.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_history_task_id", "approval_history", ["task_id"])

    op.create_table(
        "implementation_metrics",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("generated_files", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("files_changed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("additions", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("deletions", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("commits", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("tests_run", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("tests_passed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("review_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_implementation_metrics_task_id", "implementation_metrics", ["task_id"])


def downgrade() -> None:
    for tbl in (
        "implementation_metrics",
        "approval_history",
        "pull_requests",
        "test_runs",
        "review_comments",
        "code_reviews",
        "generated_changes",
        "implementation_plans",
        "development_sessions",
        "development_tasks",
    ):
        op.drop_table(tbl)
