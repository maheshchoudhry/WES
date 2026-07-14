"""Pydantic schemas for the AI Execution Engine."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.execution_enums import (
    DecisionRuleType,
    ExecutionStatus,
    HandoffStatus,
    PromptType,
    ReviewStatus,
    SOPCategory,
)
from app.domain.work_enums import Priority


# --- Prompt library -----------------------------------------------------
class PromptCreate(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=2, max_length=200)
    prompt_type: PromptType = PromptType.TASK
    content: str = Field(min_length=1)
    author: str | None = Field(default=None, max_length=160)


class PromptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    prompt_type: PromptType
    content: str
    version: int
    author: str | None
    created_at: datetime
    updated_at: datetime


# --- SOP library --------------------------------------------------------
class SOPCreate(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    title: str = Field(min_length=2, max_length=200)
    category: SOPCategory = SOPCategory.CODING
    content: str = Field(min_length=1)


class SOPRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    category: SOPCategory
    content: str
    version: int
    created_at: datetime
    updated_at: datetime


# --- Decision rules -----------------------------------------------------
class DecisionRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_role_id: uuid.UUID
    rule_type: DecisionRuleType
    name: str
    description: str | None
    authority_limit: str | None


# --- Execution queue ----------------------------------------------------
class QueueItemCreate(BaseModel):
    ai_employee_id: uuid.UUID
    work_item_id: uuid.UUID | None = None
    title: str = Field(min_length=2, max_length=300)
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    sop_id: uuid.UUID | None = None
    prompt_id: uuid.UUID | None = None


class QueueItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_employee_id: uuid.UUID
    ai_employee_name: str | None = None
    work_item_id: uuid.UUID | None
    work_item_code: str | None = None
    title: str
    description: str | None
    priority: Priority
    status: ExecutionStatus
    position: int
    sop_id: uuid.UUID | None
    prompt_id: uuid.UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class QueueAdvance(BaseModel):
    status: ExecutionStatus
    output: str | None = None


# --- Execution history --------------------------------------------------
class HistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_employee_id: uuid.UUID
    ai_employee_name: str | None = None
    work_item_id: uuid.UUID | None
    action: str
    output: str | None
    status: ExecutionStatus
    duration_seconds: int | None
    created_at: datetime


# --- Review queue -------------------------------------------------------
class ReviewCreate(BaseModel):
    work_item_id: uuid.UUID | None = None
    reviewer_ai_employee_id: uuid.UUID
    submitter_ai_employee_id: uuid.UUID | None = None
    notes: str | None = None


class ReviewDecision(BaseModel):
    status: ReviewStatus
    notes: str | None = None


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    work_item_id: uuid.UUID | None
    work_item_code: str | None = None
    reviewer_ai_employee_id: uuid.UUID
    reviewer_name: str | None = None
    submitter_ai_employee_id: uuid.UUID | None
    submitter_name: str | None = None
    status: ReviewStatus
    notes: str | None
    reviewed_at: datetime | None
    created_at: datetime


# --- Handoffs -----------------------------------------------------------
class HandoffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    work_item_id: uuid.UUID | None
    work_item_code: str | None = None
    from_ai_employee_id: uuid.UUID | None
    from_name: str | None = None
    to_ai_employee_id: uuid.UUID
    to_name: str | None = None
    stage: str
    status: HandoffStatus
    notes: str | None
    sequence: int
    created_at: datetime


class HandoffAdvance(BaseModel):
    status: HandoffStatus


# --- Execution context --------------------------------------------------
class ContextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_employee_id: uuid.UUID
    work_item_id: uuid.UUID | None
    key: str
    value: str
