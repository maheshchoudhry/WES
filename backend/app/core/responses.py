"""Standard API response envelope.

Every successful response is wrapped as ``{"data": ..., "meta": ...}`` and every
error as ``{"error": {"code", "message", "details"}}``. This is the response
standard applied across the Company Engine (API standards, Blueprint Vol. 04).
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    total: int | None = None
    page: int | None = None
    page_size: int | None = None


class DataResponse(BaseModel, Generic[T]):
    data: T
    meta: Meta | None = None


class ListResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: Meta


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] = []


class ErrorResponse(BaseModel):
    error: ErrorDetail


def ok(data: Any, meta: Meta | None = None) -> dict:
    """Build a success envelope as a plain dict (for handlers that need it)."""
    payload: dict[str, Any] = {"data": data}
    if meta is not None:
        payload["meta"] = meta.model_dump(exclude_none=True)
    return payload
