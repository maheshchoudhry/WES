"""ai execution engine schema

Creates ai_workspaces, prompt_templates, sop_library, decision_rules,
execution_queue, execution_history, review_queue, handoffs, execution_context.

Revision ID: 0005_ai_execution_engine
Revises: 0004_work_management
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0005_ai_execution_engine"
down_revision: Union[str, None] = "0004_work_management"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("prompt_type", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("author", sa.String(length=160), nullable=True),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_prompt_templates_code"),
    )
    op.create_index("ix_prompt_templates_code", "prompt_templates", ["code"])

    op.create_table(
        "sop_library",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_sop_library_code"),
    )
    op.create_index("ix_sop_library_code", "sop_library", ["code"])

    op.create_table(
        "decision_rules",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("ai_role_id", GUID(), nullable=False),
        sa.Column("rule_type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("authority_limit", sa.String(length=160), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["ai_role_id"], ["ai_roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decision_rules_ai_role_id", "decision_rules", ["ai_role_id"])

    op.create_table(
        "ai_workspaces",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("ai_employee_id", GUID(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ai_employee_id", name="uq_ai_workspaces_employee"),
    )

    op.create_table(
        "execution_queue",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("ai_employee_id", GUID(), nullable=False),
        sa.Column("work_item_id", GUID(), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("sop_id", GUID(), nullable=True),
        sa.Column("prompt_id", GUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sop_id"], ["sop_library.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["prompt_id"], ["prompt_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_execution_queue_ai_employee_id", "execution_queue", ["ai_employee_id"])
    op.create_index("ix_execution_queue_status", "execution_queue", ["status"])
    op.create_index("ix_execution_queue_work_item_id", "execution_queue", ["work_item_id"])

    op.create_table(
        "execution_history",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("ai_employee_id", GUID(), nullable=False),
        sa.Column("work_item_id", GUID(), nullable=True),
        sa.Column("execution_queue_id", GUID(), nullable=True),
        sa.Column("action", sa.String(length=160), nullable=False),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["execution_queue_id"], ["execution_queue.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_execution_history_ai_employee_id", "execution_history", ["ai_employee_id"])

    op.create_table(
        "review_queue",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("work_item_id", GUID(), nullable=True),
        sa.Column("execution_history_id", GUID(), nullable=True),
        sa.Column("reviewer_ai_employee_id", GUID(), nullable=False),
        sa.Column("submitter_ai_employee_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["execution_history_id"], ["execution_history.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewer_ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submitter_ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_queue_reviewer", "review_queue", ["reviewer_ai_employee_id"])
    op.create_index("ix_review_queue_status", "review_queue", ["status"])

    op.create_table(
        "handoffs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("work_item_id", GUID(), nullable=True),
        sa.Column("from_ai_employee_id", GUID(), nullable=True),
        sa.Column("to_ai_employee_id", GUID(), nullable=False),
        sa.Column("stage", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_handoffs_work_item_id", "handoffs", ["work_item_id"])
    op.create_index("ix_handoffs_to", "handoffs", ["to_ai_employee_id"])

    op.create_table(
        "execution_context",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("ai_employee_id", GUID(), nullable=False),
        sa.Column("work_item_id", GUID(), nullable=True),
        sa.Column("key", sa.String(length=160), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_execution_context_ai_employee_id", "execution_context", ["ai_employee_id"])


def downgrade() -> None:
    for tbl in (
        "execution_context",
        "handoffs",
        "review_queue",
        "execution_history",
        "execution_queue",
        "ai_workspaces",
        "decision_rules",
        "sop_library",
        "prompt_templates",
    ):
        op.drop_table(tbl)
