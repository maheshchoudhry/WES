"""ai work management schema

Creates projects, milestones, project_sprints, work_items, assignments,
work_dependencies, activity_log, comments, and attachments_metadata.

Revision ID: 0004_work_management
Revises: 0003_ai_company_core
Create Date: 2026-07-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0004_work_management"
down_revision: Union[str, None] = "0003_ai_company_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("owner_ai_employee_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("repository", sa.String(length=300), nullable=True),
        sa.Column("tech_stack", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        *_ts(),
        sa.ForeignKeyConstraint(["owner_ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_projects_code"),
    )
    op.create_index("ix_projects_code", "projects", ["code"])

    op.create_table(
        "milestones",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_milestones_project_id", "milestones", ["project_id"])

    op.create_table(
        "project_sprints",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("sprint_number", sa.Integer(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("velocity", sa.Integer(), nullable=False, server_default=sa.text("0")),
        *_ts(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_project_sprints_project_id", "project_sprints", ["project_id"])

    op.create_table(
        "work_items",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("acceptance_criteria", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("estimated_hours", sa.Float(), nullable=True),
        sa.Column("actual_hours", sa.Float(), nullable=True),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("sprint_id", GUID(), nullable=True),
        sa.Column("milestone_id", GUID(), nullable=True),
        sa.Column("assigned_ai_employee_id", GUID(), nullable=True),
        sa.Column("reviewer_ai_employee_id", GUID(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sprint_id"], ["project_sprints.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["milestone_id"], ["milestones.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewer_ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_code", name="uq_work_items_task_code"),
    )
    op.create_index("ix_work_items_task_code", "work_items", ["task_code"])
    op.create_index("ix_work_items_status", "work_items", ["status"])
    op.create_index("ix_work_items_project_id", "work_items", ["project_id"])
    op.create_index("ix_work_items_sprint_id", "work_items", ["sprint_id"])
    op.create_index("ix_work_items_assigned", "work_items", ["assigned_ai_employee_id"])

    op.create_table(
        "assignments",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("work_item_id", GUID(), nullable=False),
        sa.Column("ai_employee_id", GUID(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("assigned_by", sa.String(length=160), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assignments_work_item_id", "assignments", ["work_item_id"])

    op.create_table(
        "work_dependencies",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("work_item_id", GUID(), nullable=False),
        sa.Column("depends_on_id", GUID(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["depends_on_id"], ["work_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_dependencies_work_item_id", "work_dependencies", ["work_item_id"])

    op.create_table(
        "activity_log",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("work_item_id", GUID(), nullable=True),
        sa.Column("actor", sa.String(length=160), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_log_project_id", "activity_log", ["project_id"])
    op.create_index("ix_activity_log_work_item_id", "activity_log", ["work_item_id"])

    op.create_table(
        "comments",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("work_item_id", GUID(), nullable=False),
        sa.Column("author", sa.String(length=160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comments_work_item_id", "comments", ["work_item_id"])

    op.create_table(
        "attachments_metadata",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("work_item_id", GUID(), nullable=False),
        sa.Column("filename", sa.String(length=300), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attachments_metadata_work_item_id", "attachments_metadata", ["work_item_id"])


def downgrade() -> None:
    for tbl in (
        "attachments_metadata",
        "comments",
        "activity_log",
        "work_dependencies",
        "assignments",
        "work_items",
        "project_sprints",
        "milestones",
        "projects",
    ):
        op.drop_table(tbl)
