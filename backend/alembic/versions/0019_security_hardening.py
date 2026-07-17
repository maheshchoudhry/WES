"""security hardening — refresh tokens + audit log (WP5, Phase 5)

Adds ``refresh_tokens`` (per-token jti + revocation for rotation) and
``audit_log`` (privileged-action + security-event trail). Additive only.

Revision ID: 0019_security_hardening
Revises: 0018_notifications
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0019_security_hardening"
down_revision: Union[str, None] = "0018_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("jti", sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column("employee_id", GUID(), nullable=False, index=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("actor", sa.String(length=200), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False, index=True),
        sa.Column("category", sa.String(length=30), nullable=False, server_default="action", index=True),
        sa.Column("entity_type", sa.String(length=40), nullable=True),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("refresh_tokens")
