"""Shared API dependencies (pagination, service providers, auth/RBAC)."""

import uuid
from dataclasses import dataclass

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.domain.roles import Permission, Role, role_has_permission
from app.services.auth import AuthError, AuthService
from app.services.company import CompanyService
from app.services.department import DepartmentService
from app.services.employee import EmployeeService


@dataclass
class Pagination:
    offset: int
    limit: int


def pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Pagination:
    return Pagination(offset=(page - 1) * page_size, limit=page_size)


def get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    return CompanyService(db)


def get_department_service(db: Session = Depends(get_db)) -> DepartmentService:
    return DepartmentService(db)


def get_employee_service(db: Session = Depends(get_db)) -> EmployeeService:
    return EmployeeService(db)


def get_ai_org_service(db: Session = Depends(get_db)):
    from app.services.ai_organization import AIOrganizationService

    return AIOrganizationService(db)


def get_ai_reporting_service(db: Session = Depends(get_db)):
    from app.services.ai_reporting import AIReportingService

    return AIReportingService(db)


# --- Authentication / RBAC ------------------------------------------------


@dataclass
class CurrentUser:
    """The authenticated principal resolved from the access token."""

    id: uuid.UUID
    email: str
    role: Role
    full_name: str
    department_id: uuid.UUID | None


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def _bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError("Missing or invalid Authorization header")
    return token


def get_current_user(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> CurrentUser:
    """Resolve the current user from the Bearer access token (401 if invalid)."""
    employee = auth.user_from_access_token(_bearer_token(request))
    role = employee.role if isinstance(employee.role, Role) else Role(employee.role)
    return CurrentUser(
        id=employee.id,
        email=employee.email,
        role=role,
        full_name=employee.full_name,
        department_id=employee.department_id,
    )


def require_permission(permission: Permission):
    """Build a dependency that enforces ``permission`` for the current user.

    Reusable RBAC middleware: every protected endpoint declares the permission it
    needs. Missing auth -> 401 (from get_current_user); insufficient role -> 403.
    """

    def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not role_has_permission(user.role, permission):
            raise ForbiddenError(f"Role '{user.role.value}' lacks permission '{permission.value}'")
        return user

    return _guard
