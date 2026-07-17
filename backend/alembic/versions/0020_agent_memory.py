"""persistent long-term memory (WP8, Phase 6)

Creates ``agent_memories`` — durable, retrievable experience for AI employees,
projects, and the org (implementations, decisions, lessons). Survives restart
(it is in the database) and is recalled to inform future work. Additive only.

Revision ID: 0020_agent_memory
Revises: 0019_security_hardening
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0020_agent_memory"
down_revision: Union[str, None] = "0019_security_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_memories",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("scope", sa.String(length=20), nullable=False, index=True),  # employee/project/org
        sa.Column("employee_id", GUID(), nullable=True, index=True),
        sa.Column("project_id", GUID(), nullable=True, index=True),
        sa.Column("kind", sa.String(length=30), nullable=False, index=True),
        sa.Column("summary", sa.String(length=400), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("source_task_id", GUID(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("agent_memories")
