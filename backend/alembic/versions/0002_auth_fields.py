"""add authentication fields to employees

Adds RBAC/auth columns to the employees table without altering the existing
Company Engine schema. Uses batch mode so it also applies on SQLite.

Revision ID: 0002_auth_fields
Revises: 0001_initial
Create Date: 2026-07-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_auth_fields"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("employees") as batch:
        batch.add_column(
            sa.Column("role", sa.String(length=20), nullable=False, server_default="employee")
        )
        batch.add_column(sa.Column("password_hash", sa.String(length=255), nullable=True))
        batch.add_column(
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch.add_column(sa.Column("last_login", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(
            sa.Column(
                "failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")
            )
        )
        batch.add_column(
            sa.Column(
                "refresh_token_version", sa.Integer(), nullable=False, server_default=sa.text("0")
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("employees") as batch:
        batch.drop_column("refresh_token_version")
        batch.drop_column("failed_login_attempts")
        batch.drop_column("last_login")
        batch.drop_column("is_active")
        batch.drop_column("password_hash")
        batch.drop_column("role")
