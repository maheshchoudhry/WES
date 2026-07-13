"""Authentication service.

Orchestrates login, token refresh, logout, and current-user resolution. Reuses
the EmployeeRepository (Company Engine) for data access and the password/token
services for security primitives — no data-access logic is duplicated here.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import DomainError
from app.domain.roles import Role
from app.models.employee import Employee
from app.repositories.employee import EmployeeRepository
from app.schemas.auth import AuthenticatedUser, TokenPair
from app.services.password import PasswordService
from app.services.tokens import TokenError, TokenService

# Lock an account after this many consecutive failed logins.
_MAX_FAILED_ATTEMPTS = 5


class AuthError(DomainError):
    """401 — authentication failed (bad credentials, inactive, invalid token)."""

    status_code = 401
    code = "UNAUTHORIZED"


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.employees = EmployeeRepository(db)
        self.passwords = PasswordService()
        self.tokens = TokenService()
        self.settings = get_settings()

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _to_user(employee: Employee) -> AuthenticatedUser:
        role = employee.role.value if hasattr(employee.role, "value") else employee.role
        status = employee.status.value if hasattr(employee.status, "value") else employee.status
        return AuthenticatedUser(
            id=employee.id,
            employee_code=employee.employee_code,
            full_name=employee.full_name,
            email=employee.email,
            role=str(role),
            department_id=employee.department_id,
            status=str(status),
        )

    def _issue_tokens(self, employee: Employee, *, remember: bool) -> TokenPair:
        role = employee.role.value if hasattr(employee.role, "value") else employee.role
        access = self.tokens.create_access_token(
            subject=employee.id, role=str(role), email=employee.email
        )
        refresh = self.tokens.create_refresh_token(
            subject=employee.id, version=employee.refresh_token_version, remember=remember
        )
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=self.settings.access_token_minutes * 60,
        )

    # -- public API --------------------------------------------------------

    def login(self, email: str, password: str, *, remember: bool = False):
        employee = self.employees.get_by_email(email)
        # Uniform error to avoid revealing which part failed.
        if employee is None:
            raise AuthError("Invalid email or password")
        if not employee.is_active:
            raise AuthError("Account is disabled")
        if employee.failed_login_attempts >= _MAX_FAILED_ATTEMPTS:
            raise AuthError("Account is locked due to too many failed attempts")

        if not self.passwords.verify(password, employee.password_hash):
            employee.failed_login_attempts += 1
            self.db.flush()
            raise AuthError("Invalid email or password")

        employee.failed_login_attempts = 0
        employee.last_login = datetime.now(timezone.utc)
        self.db.flush()

        tokens = self._issue_tokens(employee, remember=remember)
        return self._to_user(employee), tokens

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            claims = self.tokens.decode_refresh(refresh_token)
        except TokenError as exc:
            raise AuthError(str(exc)) from exc

        employee = self.employees.get(claims.subject)
        if employee is None or not employee.is_active:
            raise AuthError("Account not found or disabled")
        # A logout bumps refresh_token_version, invalidating older refresh tokens.
        if claims.version != employee.refresh_token_version:
            raise AuthError("Refresh token has been revoked")

        return self._issue_tokens(employee, remember=False)

    def logout(self, employee_id: uuid.UUID) -> None:
        """Invalidate all outstanding refresh tokens for the employee."""
        employee = self.employees.get(employee_id)
        if employee is not None:
            employee.refresh_token_version += 1
            self.db.flush()

    def user_from_access_token(self, token: str) -> Employee:
        """Resolve and validate the employee behind an access token."""
        try:
            claims = self.tokens.decode_access(token)
        except TokenError as exc:
            raise AuthError(str(exc)) from exc
        employee = self.employees.get(claims.subject)
        if employee is None or not employee.is_active:
            raise AuthError("Account not found or disabled")
        return employee

    def current_user(self, token: str) -> AuthenticatedUser:
        return self._to_user(self.user_from_access_token(token))

    def authenticated_user(self, employee_id: uuid.UUID) -> AuthenticatedUser:
        """Serialize an already-authenticated employee by id."""
        employee = self.employees.get(employee_id)
        if employee is None:
            raise AuthError("Account not found")
        return self._to_user(employee)
