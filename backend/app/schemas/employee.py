"""Employee request/response schemas and field validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domain.enums import AuthorityLevel, EmployeeStatus


class EmployeeBase(BaseModel):
    employee_code: str = Field(min_length=1, max_length=40)
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    position: str = Field(min_length=2, max_length=160)
    authority: AuthorityLevel = AuthorityLevel.OPERATIONAL
    status: EmployeeStatus = EmployeeStatus.ONBOARDING

    @field_validator("employee_code")
    @classmethod
    def _code_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("employee_code must not be blank")
        return v

    @field_validator("full_name", "position")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class EmployeeCreate(EmployeeBase):
    """Employee registration payload."""

    company_id: uuid.UUID
    department_id: uuid.UUID | None = None
    reports_to_id: uuid.UUID | None = None


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    email: EmailStr | None = None
    position: str | None = Field(default=None, min_length=2, max_length=160)
    authority: AuthorityLevel | None = None
    status: EmployeeStatus | None = None
    reports_to_id: uuid.UUID | None = None


class EmployeeAssignDepartment(BaseModel):
    """Assign (or clear) an employee's department."""

    department_id: uuid.UUID | None = None


class EmployeeRead(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    department_id: uuid.UUID | None
    reports_to_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
