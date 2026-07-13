"""Company request/response schemas and field validation."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import EntityStatus

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CompanyBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=160)
    company_type: str = Field(min_length=2, max_length=120)
    purpose: str | None = Field(default=None, max_length=2000)
    description: str | None = Field(default=None, max_length=4000)
    status: EntityStatus = EntityStatus.ACTIVE

    @field_validator("name", "company_type")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("slug")
    @classmethod
    def _slug_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not _SLUG_RE.match(v):
            raise ValueError("slug must be lowercase alphanumeric words separated by hyphens")
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    """Partial update; all fields optional."""

    name: str | None = Field(default=None, min_length=2, max_length=160)
    company_type: str | None = Field(default=None, min_length=2, max_length=120)
    purpose: str | None = Field(default=None, max_length=2000)
    description: str | None = Field(default=None, max_length=4000)
    status: EntityStatus | None = None


class CompanyRead(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
