"""Shared schema base and pagination envelope."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(BaseModel):
    """Base model: camelCase JSON aliases, populated from ORM attributes."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class PageMeta(CamelModel):
    page: int
    page_size: int
    total: int


class Page(CamelModel, Generic[T]):
    data: list[T]
    pagination: PageMeta
