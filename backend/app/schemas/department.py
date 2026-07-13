"""Department request/response schemas and field validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import EntityStatus


class DepartmentBase(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=160)
    focus: str | None = Field(default=None, max_length=2000)
    status: EntityStatus = EntityStatus.ACTIVE

    @field_validator("code")
    @classmethod
    def _code_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("code must not be blank")
        return v

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class DepartmentCreate(DepartmentBase):
    company_id: uuid.UUID


class DepartmentUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=40)
    name: str | None = Field(default=None, min_length=2, max_length=160)
    focus: str | None = Field(default=None, max_length=2000)
    status: EntityStatus | None = None

    @field_validator("code")
    @classmethod
    def _code_upper(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else v


class DepartmentRead(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
