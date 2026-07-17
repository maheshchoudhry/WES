"""self-learning rules (WP9, Phase 7)

Creates ``learning_rules`` — reusable rules the company derives from completed
work (lessons, bug-prevention, coding-standard, architecture) and applies to
future tasks. Additive only.

Revision ID: 0021_self_learning
Revises: 0020_agent_memory
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0021_self_learning"
down_revision: Union[str, None] = "0020_agent_memory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_rules",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("kind", sa.String(length=30), nullable=False, index=True),
        sa.Column("rule", sa.String(length=500), nullable=False, unique=True),
        sa.Column("dimension", sa.String(length=40), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("occurrences", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("applied_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source_task_id", GUID(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("learning_rules")
