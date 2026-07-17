"""durable background execution — jobs queue (WP3, Phase 2)

Creates the ``jobs`` table: a persistent, DB-backed work queue so long-running
autonomous work survives process restarts (resume), supports retry / cancel /
pause / resume, and records execution history + progress. Additive only — no
existing table is modified.

Revision ID: 0016_durable_jobs
Revises: 0015_project_intake
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0016_durable_jobs"
down_revision: Union[str, None] = "0015_project_intake"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("job_type", sa.String(length=60), nullable=False, index=True),
        sa.Column("payload", sa.Text(), nullable=True),  # JSON
        sa.Column("status", sa.String(length=20), nullable=False, index=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_message", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),  # JSON
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("worker_id", sa.String(length=80), nullable=True),
        sa.Column("idempotency_key", sa.String(length=200), nullable=True, unique=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("jobs")
