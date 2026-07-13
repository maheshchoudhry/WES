"""Domain-level exceptions and their HTTP mapping.

Services raise these framework-agnostic exceptions; a FastAPI exception handler
(see ``app.main``) translates them into the standard error envelope. This keeps
the service layer free of HTTP concerns.
"""


class DomainError(Exception):
    """Base class for all domain errors."""

    status_code: int = 400
    code: str = "DOMAIN_ERROR"

    def __init__(self, message: str, details: list[dict] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or []


class NotFoundError(DomainError):
    """A requested entity does not exist."""

    status_code = 404
    code = "NOT_FOUND"


class ConflictError(DomainError):
    """The request conflicts with the current state (e.g. duplicate, in-use)."""

    status_code = 409
    code = "CONFLICT"


class ValidationError(DomainError):
    """A business-rule validation failed."""

    status_code = 422
    code = "VALIDATION_ERROR"
