"""real AI-employee orchestration + handoffs (WP7, Phase 3)

Adds ``acting_ai_employee_id`` to ``development_sessions`` (which REAL employee
performed the stage) and creates ``development_handoffs`` (the recorded handoff of
work between employees). Additive + nullable -> backward compatible.

Revision ID: 0017_ai_orchestration
Revises: 0016_durable_jobs
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0017_ai_orchestration"
down_revision: Union[str, None] = "0016_durable_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "development_sessions",
        sa.Column("acting_ai_employee_id", GUID(), nullable=True),
    )
    op.add_column(
        "development_sessions",
        sa.Column("provider_name", sa.String(length=60), nullable=True),
    )
    op.create_table(
        "development_handoffs",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("task_id", GUID(), nullable=False, index=True),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("from_employee_id", GUID(), nullable=True),
        sa.Column("to_employee_id", GUID(), nullable=True),
        sa.Column("from_role", sa.String(length=160), nullable=True),
        sa.Column("to_role", sa.String(length=160), nullable=True),
        sa.Column("stage", sa.String(length=40), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("development_handoffs")
    op.drop_column("development_sessions", "provider_name")
    op.drop_column("development_sessions", "acting_ai_employee_id")
