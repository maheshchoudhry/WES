"""Pydantic schemas for the AI Work Management engine."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.work_enums import (
    AssignmentRole,
    DependencyType,
    MilestoneStatus,
    Priority,
    ProjectStatus,
    SprintStatus,
    WorkStatus,
)


# --- Projects -----------------------------------------------------------
class ProjectCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=200)
    owner_ai_employee_id: uuid.UUID | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    priority: Priority = Priority.MEDIUM
    repository: str | None = Field(default=None, max_length=300)
    tech_stack: str | None = None

    @field_validator("code")
    @classmethod
    def _code_upper(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("code must not be blank")
        return v


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    owner_ai_employee_id: uuid.UUID | None = None
    status: ProjectStatus | None = None
    priority: Priority | None = None
    repository: str | None = Field(default=None, max_length=300)
    tech_stack: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    owner_ai_employee_id: uuid.UUID | None
    owner_name: str | None = None
    status: ProjectStatus
    priority: Priority
    repository: str | None
    tech_stack: str | None
    version: int
    task_count: int = 0
    created_at: datetime
    updated_at: datetime


# --- Milestones ---------------------------------------------------------
class MilestoneCreate(BaseModel):
    project_id: uuid.UUID
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    due_date: date | None = None
    status: MilestoneStatus = MilestoneStatus.PENDING


class MilestoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    due_date: date | None = None
    status: MilestoneStatus | None = None


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    due_date: date | None
    status: MilestoneStatus
    created_at: datetime
    updated_at: datetime


# --- Sprints ------------------------------------------------------------
class SprintCreate(BaseModel):
    project_id: uuid.UUID
    sprint_number: int = Field(ge=1)
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: SprintStatus = SprintStatus.PLANNED
    velocity: int = Field(default=0, ge=0)


class SprintUpdate(BaseModel):
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: SprintStatus | None = None
    velocity: int | None = Field(default=None, ge=0)


class SprintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    sprint_number: int
    goal: str | None
    start_date: date | None
    end_date: date | None
    status: SprintStatus
    velocity: int
    task_count: int = 0
    done_count: int = 0
    created_at: datetime
    updated_at: datetime


# --- Work items (tasks) -------------------------------------------------
class WorkItemCreate(BaseModel):
    task_code: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=2, max_length=300)
    description: str | None = None
    acceptance_criteria: str | None = None
    priority: Priority = Priority.MEDIUM
    status: WorkStatus = WorkStatus.BACKLOG
    estimated_hours: float | None = Field(default=None, ge=0)
    actual_hours: float | None = Field(default=None, ge=0)
    project_id: uuid.UUID
    sprint_id: uuid.UUID | None = None
    milestone_id: uuid.UUID | None = None
    assigned_ai_employee_id: uuid.UUID | None = None
    reviewer_ai_employee_id: uuid.UUID | None = None

    @field_validator("task_code")
    @classmethod
    def _code_upper(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("task_code must not be blank")
        return v


class WorkItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=300)
    description: str | None = None
    acceptance_criteria: str | None = None
    priority: Priority | None = None
    status: WorkStatus | None = None
    estimated_hours: float | None = Field(default=None, ge=0)
    actual_hours: float | None = Field(default=None, ge=0)
    sprint_id: uuid.UUID | None = None
    milestone_id: uuid.UUID | None = None
    assigned_ai_employee_id: uuid.UUID | None = None
    reviewer_ai_employee_id: uuid.UUID | None = None


class WorkItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_code: str
    title: str
    description: str | None
    acceptance_criteria: str | None
    priority: Priority
    status: WorkStatus
    estimated_hours: float | None
    actual_hours: float | None
    project_id: uuid.UUID
    project_code: str | None = None
    sprint_id: uuid.UUID | None
    sprint_number: int | None = None
    milestone_id: uuid.UUID | None
    milestone_name: str | None = None
    assigned_ai_employee_id: uuid.UUID | None
    assigned_name: str | None = None
    reviewer_ai_employee_id: uuid.UUID | None
    reviewer_name: str | None = None
    created_at: datetime
    updated_at: datetime


# --- Assignments / dependencies / comments / activity -------------------
class AssignmentCreate(BaseModel):
    ai_employee_id: uuid.UUID
    role: AssignmentRole = AssignmentRole.ASSIGNEE


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    work_item_id: uuid.UUID
    ai_employee_id: uuid.UUID
    ai_employee_name: str | None = None
    role: AssignmentRole
    assigned_by: str | None
    created_at: datetime


class DependencyCreate(BaseModel):
    depends_on_id: uuid.UUID
    type: DependencyType = DependencyType.BLOCKS


class DependencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    work_item_id: uuid.UUID
    depends_on_id: uuid.UUID
    depends_on_code: str | None = None
    type: DependencyType


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    author: str | None = None


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    work_item_id: uuid.UUID
    author: str
    body: str
    created_at: datetime


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    work_item_id: uuid.UUID | None
    actor: str
    action: str
    detail: str | None
    created_at: datetime
