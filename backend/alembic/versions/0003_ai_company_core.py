"""ai company core schema

Creates the AI organization tables: ai_departments, ai_roles, ai_capabilities,
ai_employees (self-referential reporting), ai_responsibilities, ai_kpis, and the
ai_employee_capabilities association.

Revision ID: 0003_ai_company_core
Revises: 0002_auth_fields
Create Date: 2026-07-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0003_ai_company_core"
down_revision: Union[str, None] = "0002_auth_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "ai_departments",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("focus", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_ai_departments_code"),
        sa.UniqueConstraint("name", name="uq_ai_departments_name"),
    )
    op.create_index("ix_ai_departments_code", "ai_departments", ["code"])

    op.create_table(
        "ai_roles",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_executive_head", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_ai_roles_code"),
    )
    op.create_index("ix_ai_roles_code", "ai_roles", ["code"])

    op.create_table(
        "ai_capabilities",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_ai_capabilities_code"),
    )
    op.create_index("ix_ai_capabilities_code", "ai_capabilities", ["code"])

    op.create_table(
        "ai_employees",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("employee_code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("department_id", GUID(), nullable=False),
        sa.Column("role_id", GUID(), nullable=False),
        sa.Column("manager_id", GUID(), nullable=True),
        sa.Column("authority", sa.String(length=20), nullable=False),
        sa.Column("decision_scope", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_ts(),
        sa.ForeignKeyConstraint(["department_id"], ["ai_departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["role_id"], ["ai_roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["manager_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_code", name="uq_ai_employees_employee_code"),
    )
    op.create_index("ix_ai_employees_employee_code", "ai_employees", ["employee_code"])
    op.create_index("ix_ai_employees_department_id", "ai_employees", ["department_id"])
    op.create_index("ix_ai_employees_role_id", "ai_employees", ["role_id"])
    op.create_index("ix_ai_employees_is_deleted", "ai_employees", ["is_deleted"])

    op.create_table(
        "ai_responsibilities",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("ai_employee_id", GUID(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        *_ts(),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_responsibilities_ai_employee_id", "ai_responsibilities", ["ai_employee_id"])

    op.create_table(
        "ai_kpis",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("ai_employee_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("target", sa.String(length=120), nullable=True),
        sa.Column("unit", sa.String(length=60), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_kpis_ai_employee_id", "ai_kpis", ["ai_employee_id"])

    op.create_table(
        "ai_employee_capabilities",
        sa.Column("ai_employee_id", GUID(), nullable=False),
        sa.Column("ai_capability_id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ai_capability_id"], ["ai_capabilities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ai_employee_id", "ai_capability_id"),
    )


def downgrade() -> None:
    op.drop_table("ai_employee_capabilities")
    op.drop_table("ai_kpis")
    op.drop_table("ai_responsibilities")
    op.drop_table("ai_employees")
    op.drop_table("ai_capabilities")
    op.drop_table("ai_roles")
    op.drop_table("ai_departments")
