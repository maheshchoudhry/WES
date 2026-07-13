"""Pydantic schemas for the AI Company Core."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.ai_enums import AIDecisionAuthority, AIEmployeeStatus, AIRoleLevel
from app.domain.enums import EntityStatus


class AIDepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    focus: str | None
    status: EntityStatus
    created_at: datetime
    updated_at: datetime


class AIRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    level: AIRoleLevel
    description: str | None
    is_executive_head: bool
    created_at: datetime
    updated_at: datetime


class AICapabilityRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str


class AIKPIInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    target: str | None = Field(default=None, max_length=120)
    unit: str | None = Field(default=None, max_length=60)


class AIKPIRead(AIKPIInput):
    model_config = ConfigDict(from_attributes=True)


class AIEmployeeBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    authority: AIDecisionAuthority = AIDecisionAuthority.OPERATIONAL
    decision_scope: str | None = Field(default=None, max_length=2000)
    status: AIEmployeeStatus = AIEmployeeStatus.ACTIVE

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class AIEmployeeCreate(AIEmployeeBase):
    employee_code: str = Field(min_length=1, max_length=40)
    department_id: uuid.UUID
    role_id: uuid.UUID
    manager_id: uuid.UUID | None = None
    responsibilities: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)  # capability codes
    kpis: list[AIKPIInput] = Field(default_factory=list)

    @field_validator("employee_code")
    @classmethod
    def _code_upper(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("employee_code must not be blank")
        return v


class AIEmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    department_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    manager_id: uuid.UUID | None = None
    authority: AIDecisionAuthority | None = None
    decision_scope: str | None = Field(default=None, max_length=2000)
    status: AIEmployeeStatus | None = None
    responsibilities: list[str] | None = None
    capabilities: list[str] | None = None
    kpis: list[AIKPIInput] | None = None


class AIEmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_code: str
    name: str
    department_id: uuid.UUID
    department_name: str | None = None
    role_id: uuid.UUID
    role_title: str | None = None
    role_level: str | None = None
    manager_id: uuid.UUID | None
    manager_name: str | None = None
    authority: AIDecisionAuthority
    decision_scope: str | None
    status: AIEmployeeStatus
    version: int
    responsibilities: list[str] = Field(default_factory=list)
    capabilities: list[AICapabilityRef] = Field(default_factory=list)
    kpis: list[AIKPIRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
