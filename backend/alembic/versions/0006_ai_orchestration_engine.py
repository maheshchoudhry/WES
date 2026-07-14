"""ai orchestration engine schema

Creates ai_providers, provider_configs, conversation_threads, execution_runs,
execution_messages, execution_metrics, token_usage, cost_tracking,
provider_health, and retry_history.

Revision ID: 0006_ai_orchestration_engine
Revises: 0005_ai_execution_engine
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0006_ai_orchestration_engine"
down_revision: Union[str, None] = "0005_ai_execution_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def _created():
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "ai_providers",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("default_model", sa.String(length=120), nullable=True),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_ai_providers_name"),
    )
    op.create_index("ix_ai_providers_name", "ai_providers", ["name"])

    op.create_table(
        "provider_configs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_configs_provider_id", "provider_configs", ["provider_id"])

    op.create_table(
        "conversation_threads",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("ai_employee_id", GUID(), nullable=True),
        sa.Column("work_item_id", GUID(), nullable=True),
        sa.Column("provider_id", GUID(), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversation_threads_ai_employee_id", "conversation_threads", ["ai_employee_id"])

    op.create_table(
        "execution_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("thread_id", GUID(), nullable=True),
        sa.Column("ai_employee_id", GUID(), nullable=True),
        sa.Column("work_item_id", GUID(), nullable=True),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("review_outcome", sa.String(length=20), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["thread_id"], ["conversation_threads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_execution_runs_status", "execution_runs", ["status"])
    op.create_index("ix_execution_runs_provider_id", "execution_runs", ["provider_id"])
    op.create_index("ix_execution_runs_thread_id", "execution_runs", ["thread_id"])

    op.create_table(
        "execution_messages",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("thread_id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("0")),
        _created(),
        sa.ForeignKeyConstraint(["thread_id"], ["conversation_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_execution_messages_thread_id", "execution_messages", ["thread_id"])

    op.create_table(
        "execution_metrics",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        _created(),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_execution_metrics_run_id", "execution_metrics", ["run_id"])

    op.create_table(
        "token_usage",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=True),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("ai_employee_id", GUID(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        _created(),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_token_usage_provider_id", "token_usage", ["provider_id"])

    op.create_table(
        "cost_tracking",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=True),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        _created(),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cost_tracking_provider_id", "cost_tracking", ["provider_id"])

    op.create_table(
        "provider_health",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_health_provider_id", "provider_health", ["provider_id"])

    op.create_table(
        "retry_history",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_retry_history_run_id", "retry_history", ["run_id"])


def downgrade() -> None:
    for tbl in (
        "retry_history",
        "provider_health",
        "cost_tracking",
        "token_usage",
        "execution_metrics",
        "execution_messages",
        "execution_runs",
        "conversation_threads",
        "provider_configs",
        "ai_providers",
    ):
        op.drop_table(tbl)
