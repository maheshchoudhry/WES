"""Company request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import CamelModel


class CompanyBase(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    legal_type: str = Field(default="AI Engineering Company", max_length=120)
    purpose: str | None = None
    mission: str | None = None
    description: str | None = None
    status: str = Field(default="active", max_length=50)
    settings: dict = Field(default_factory=dict)
    version: str = Field(default="v1.0", max_length=20)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    legal_type: str | None = Field(default=None, max_length=120)
    purpose: str | None = None
    mission: str | None = None
    description: str | None = None
    status: str | None = Field(default=None, max_length=50)
    settings: dict | None = None
    version: str | None = Field(default=None, max_length=20)


class CompanyRead(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
