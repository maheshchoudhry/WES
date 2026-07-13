"""AI Work Management ORM models (Sprint 07).

Projects, milestones, sprints, work items (tasks), assignments, dependencies,
activity log, comments, and attachment metadata. Related entity names are
resolved in the service layer, so models stay as plain columns.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.work_enums import (
    AssignmentRole,
    DependencyType,
    MilestoneStatus,
    Priority,
    ProjectStatus,
    SprintStatus,
    WorkStatus,
)
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ProjectStatus] = mapped_column(
        String(20), nullable=False, default=ProjectStatus.PLANNING
    )
    priority: Mapped[Priority] = mapped_column(String(20), nullable=False, default=Priority.MEDIUM)
    repository: Mapped[str | None] = mapped_column(String(300), nullable=True)
    tech_stack: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Milestone(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "milestones"

    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[MilestoneStatus] = mapped_column(
        String(20), nullable=False, default=MilestoneStatus.PENDING
    )


class ProjectSprint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_sprints"

    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sprint_number: Mapped[int] = mapped_column(Integer, nullable=False)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[SprintStatus] = mapped_column(
        String(20), nullable=False, default=SprintStatus.PLANNED
    )
    velocity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class WorkItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "work_items"

    task_code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[Priority] = mapped_column(String(20), nullable=False, default=Priority.MEDIUM)
    status: Mapped[WorkStatus] = mapped_column(
        String(20), nullable=False, default=WorkStatus.BACKLOG, index=True
    )
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sprint_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("project_sprints.id", ondelete="SET NULL"), nullable=True, index=True
    )
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True
    )
    assigned_ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewer_ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )


class Assignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assignments"

    work_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[AssignmentRole] = mapped_column(
        String(20), nullable=False, default=AssignmentRole.ASSIGNEE
    )
    assigned_by: Mapped[str | None] = mapped_column(String(160), nullable=True)


class WorkDependency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "work_dependencies"

    work_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    depends_on_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[DependencyType] = mapped_column(
        String(20), nullable=False, default=DependencyType.BLOCKS
    )


class ActivityLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "activity_log"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="CASCADE"), nullable=True, index=True
    )
    actor: Mapped[str] = mapped_column(String(160), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Comment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "comments"

    work_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class AttachmentMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attachments_metadata"

    work_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
