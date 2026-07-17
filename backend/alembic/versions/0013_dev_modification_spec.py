"""development task modification spec (WP1 integration)

Adds ``modification_spec`` (JSON text) to ``development_tasks`` so an autonomous
task can carry an existing-code modification intent (target file + operation +
anchor/snippet/symbol), enabling the workflow to choose CREATE / MODIFY / DELETE /
RENAME instead of only scaffolding new files.

Revision ID: 0013_dev_modification_spec
Revises: 0012_enterprise_devops
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_dev_modification_spec"
down_revision: Union[str, None] = "0012_enterprise_devops"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "development_tasks",
        sa.Column("modification_spec", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("development_tasks", "modification_spec")
