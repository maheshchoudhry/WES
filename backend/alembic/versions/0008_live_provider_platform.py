"""live provider platform schema

Adds active_model/priority to ai_providers and creates provider_secrets,
provider_models, provider_usage, provider_billing, provider_latency,
provider_errors, provider_events, and budget_configs.

Revision ID: 0008_live_provider_platform
Revises: 0007_organizational_knowledge_engine
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0008_live_provider_platform"
down_revision: Union[str, None] = "0007_organizational_knowledge_engine"
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
    op.add_column(
        "ai_providers", sa.Column("active_model", sa.String(length=120), nullable=True)
    )
    op.add_column(
        "ai_providers",
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
    )

    op.create_table(
        "provider_secrets",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False, server_default="development"),
        sa.Column("key_name", sa.String(length=60), nullable=False, server_default="api_key"),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("hint", sa.String(length=60), nullable=True),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_secrets_provider_id", "provider_secrets", ["provider_id"])

    op.create_table(
        "provider_models",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("context_window", sa.Integer(), nullable=True),
        sa.Column("input_cost_per_1k", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("output_cost_per_1k", sa.Float(), nullable=False, server_default=sa.text("0")),
        *_ts(),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_models_provider_id", "provider_models", ["provider_id"])

    op.create_table(
        "provider_usage",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=True),
        sa.Column("ai_employee_id", GUID(), nullable=True),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("actual_cost", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("day", sa.String(length=10), nullable=False),
        sa.Column("month", sa.String(length=7), nullable=False),
        _created(),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_usage_provider_id", "provider_usage", ["provider_id"])
    op.create_index("ix_provider_usage_ai_employee_id", "provider_usage", ["ai_employee_id"])
    op.create_index("ix_provider_usage_project_id", "provider_usage", ["project_id"])
    op.create_index("ix_provider_usage_day", "provider_usage", ["day"])
    op.create_index("ix_provider_usage_month", "provider_usage", ["month"])

    op.create_table(
        "provider_billing",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("period", sa.String(length=10), nullable=False),
        sa.Column("period_key", sa.String(length=10), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cost", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_billing_provider_id", "provider_billing", ["provider_id"])
    op.create_index("ix_provider_billing_period_key", "provider_billing", ["period_key"])

    op.create_table(
        "provider_latency",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        _created(),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_latency_provider_id", "provider_latency", ["provider_id"])

    op.create_table(
        "provider_errors",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=True),
        sa.Column("error_type", sa.String(length=40), nullable=False, server_default="error"),
        sa.Column("message", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["execution_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_errors_provider_id", "provider_errors", ["provider_id"])

    op.create_table(
        "provider_events",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider_id", GUID(), nullable=True),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("actor", sa.String(length=200), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        _created(),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_events_provider_id", "provider_events", ["provider_id"])
    op.create_index("ix_provider_events_event_type", "provider_events", ["event_type"])

    op.create_table(
        "budget_configs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("scope", sa.String(length=40), nullable=False, server_default="global"),
        sa.Column("daily_cost_limit", sa.Float(), nullable=True),
        sa.Column("monthly_cost_limit", sa.Float(), nullable=True),
        sa.Column("max_cost", sa.Float(), nullable=True),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("warning_threshold", sa.Float(), nullable=False, server_default=sa.text("0.8")),
        sa.Column("hard_stop", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope", name="uq_budget_configs_scope"),
    )


def downgrade() -> None:
    for tbl in (
        "budget_configs",
        "provider_events",
        "provider_errors",
        "provider_latency",
        "provider_billing",
        "provider_usage",
        "provider_models",
        "provider_secrets",
    ):
        op.drop_table(tbl)
    op.drop_column("ai_providers", "priority")
    op.drop_column("ai_providers", "active_model")
