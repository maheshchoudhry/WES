"""founder project intake + decomposition plan (WP6, Phase 1)

Extends ``projects`` with Founder Project Intake fields and a decomposition
plan state. All columns are nullable -> fully backward compatible; existing
project creation (code + name) is unaffected.

Revision ID: 0015_project_intake
Revises: 0014_plan_requirements
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_project_intake"
down_revision: Union[str, None] = "0014_plan_requirements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMNS = [
    ("business_objective", sa.Text()),
    ("business_problem", sa.Text()),
    ("intake_description", sa.Text()),
    ("deliverables", sa.Text()),  # JSON
    ("acceptance_criteria", sa.Text()),  # JSON
    ("constraints", sa.Text()),  # JSON
    ("timeline", sa.String(length=200)),
    ("knowledge_references", sa.Text()),  # JSON
    ("attachments", sa.Text()),  # JSON
    ("founder_notes", sa.Text()),
    ("plan_status", sa.String(length=20)),
    ("business_analysis", sa.Text()),  # JSON
]


def upgrade() -> None:
    for name, type_ in _COLUMNS:
        op.add_column("projects", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.drop_column("projects", name)
