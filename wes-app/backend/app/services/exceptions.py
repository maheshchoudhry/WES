"""Service-layer exceptions mapped to HTTP responses."""
from __future__ import annotations


class ServiceError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str, details: dict | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(ServiceError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(ServiceError):
    status_code = 409
    code = "CONFLICT"
