"""implementation plan requirements + verification (semantic planning gap)

Adds ``requirements`` and ``verification`` (JSON text) to ``implementation_plans``
so the planner can persist the concrete requirements extracted from a task and the
verification report that gates the pull request.

Revision ID: 0014_plan_requirements
Revises: 0013_dev_modification_spec
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014_plan_requirements"
down_revision: Union[str, None] = "0013_dev_modification_spec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("implementation_plans", sa.Column("requirements", sa.Text(), nullable=True))
    op.add_column("implementation_plans", sa.Column("verification", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("implementation_plans", "verification")
    op.drop_column("implementation_plans", "requirements")
