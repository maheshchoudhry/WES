"""founder notifications (Phase 4 — autonomous chain)

Creates the ``notifications`` table so the Founder is notified of autonomous
milestones (tasks needing approval, deployments completed). Additive only.

Revision ID: 0018_notifications
Revises: 0017_ai_orchestration
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0018_notifications"
down_revision: Union[str, None] = "0017_ai_orchestration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("kind", sa.String(length=40), nullable=False, index=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("entity_type", sa.String(length=40), nullable=True),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("notifications")
