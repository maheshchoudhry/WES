"""Employee request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import CamelModel


class EmployeeBase(CamelModel):
    employee_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    position: str = Field(min_length=1, max_length=255)
    department_id: int | None = None
    reports_to: str | None = Field(default=None, max_length=255)
    authority_level: str = Field(default="Operational", max_length=80)
    status: str = Field(default="active", max_length=50)
    availability_status: str = Field(default="available", max_length=50)
    operational_state: str = Field(default="available", max_length=50)
    version: str = Field(default="v1.0", max_length=20)


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(CamelModel):
    employee_code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    position: str | None = Field(default=None, min_length=1, max_length=255)
    department_id: int | None = None
    reports_to: str | None = Field(default=None, max_length=255)
    authority_level: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, max_length=50)
    availability_status: str | None = Field(default=None, max_length=50)
    operational_state: str | None = Field(default=None, max_length=50)
    version: str | None = Field(default=None, max_length=20)


class EmployeeRead(EmployeeBase):
    id: int
    department_name: str | None = None
    created_at: datetime
    updated_at: datetime
