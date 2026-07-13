"""initial company engine schema

Creates the companies, departments, and employees tables that make up the WES
Core Company Engine.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("company_type", sa.String(length=120), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_companies_name"),
        sa.UniqueConstraint("slug", name="uq_companies_slug"),
    )
    op.create_index("ix_companies_name", "companies", ["name"])
    op.create_index("ix_companies_slug", "companies", ["slug"])

    op.create_table(
        "departments",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("company_id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("focus", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "code", name="uq_department_company_code"),
        sa.UniqueConstraint("company_id", "name", name="uq_department_company_name"),
    )
    op.create_index("ix_departments_company_id", "departments", ["company_id"])

    op.create_table(
        "employees",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("company_id", GUID(), nullable=False),
        sa.Column("department_id", GUID(), nullable=True),
        sa.Column("reports_to_id", GUID(), nullable=True),
        sa.Column("employee_code", sa.String(length=40), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("position", sa.String(length=160), nullable=False),
        sa.Column("authority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reports_to_id"], ["employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_code", name="uq_employees_employee_code"),
        sa.UniqueConstraint("email", name="uq_employees_email"),
    )
    op.create_index("ix_employees_company_id", "employees", ["company_id"])
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_index("ix_employees_employee_code", "employees", ["employee_code"])
    op.create_index("ix_employees_email", "employees", ["email"])


def downgrade() -> None:
    op.drop_table("employees")
    op.drop_table("departments")
    op.drop_table("companies")
