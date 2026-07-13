"""Department request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import CamelModel


class DepartmentBase(CamelModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    focus: str | None = None
    description: str | None = None
    status: str = Field(default="active", max_length=50)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(CamelModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    focus: str | None = None
    description: str | None = None
    status: str | None = Field(default=None, max_length=50)


class DepartmentRead(DepartmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
