"""Roles and permissions (RBAC) for WES OS.

Defines the five WES OS roles and the permissions each role holds. Endpoints
declare a required ``Permission``; the RBAC dependency checks it against the
current user's role using ``role_has_permission``.
"""

from enum import Enum


class Role(str, Enum):
    """WES OS access roles, from most to least privileged."""

    FOUNDER = "founder"
    DIRECTOR = "director"
    DEPARTMENT_HEAD = "department_head"
    EMPLOYEE = "employee"
    READ_ONLY = "read_only"


class Permission(str, Enum):
    """Fine-grained capabilities checked by the RBAC middleware."""

    COMPANY_READ = "company:read"
    COMPANY_WRITE = "company:write"
    DEPARTMENT_READ = "department:read"
    DEPARTMENT_WRITE = "department:write"
    EMPLOYEE_READ = "employee:read"
    EMPLOYEE_WRITE = "employee:write"
    DASHBOARD_READ = "dashboard:read"
    SELF_READ = "self:read"
    # AI Company Core (Sprint 06)
    AI_READ = "ai:read"
    AI_UPDATE = "ai:update"  # edit existing AI employees
    AI_MANAGE = "ai:manage"  # create / delete AI employees
    # Work Management (Sprint 07)
    WORK_READ = "work:read"
    WORK_WRITE = "work:write"  # create / update / delete projects, sprints, tasks


# Read permissions are granted to every authenticated role so the workspace and
# dashboard are viewable; write permissions are graded by role.
_READS = {
    Permission.COMPANY_READ,
    Permission.DEPARTMENT_READ,
    Permission.EMPLOYEE_READ,
    Permission.DASHBOARD_READ,
    Permission.SELF_READ,
    Permission.AI_READ,
    Permission.WORK_READ,
}

ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    # Full access to everything.
    Role.FOUNDER: set(Permission),
    # Project management: manages departments, employees, AI org, and work.
    Role.DIRECTOR: _READS
    | {
        Permission.DEPARTMENT_WRITE,
        Permission.EMPLOYEE_WRITE,
        Permission.AI_UPDATE,
        Permission.WORK_WRITE,
    },
    # Department management: manages employees, AI org, and department work.
    Role.DEPARTMENT_HEAD: _READS
    | {Permission.EMPLOYEE_WRITE, Permission.AI_UPDATE, Permission.WORK_WRITE},
    # Self workspace: read-only across the workspace (view assigned work).
    Role.EMPLOYEE: set(_READS),
    # Read-only access.
    Role.READ_ONLY: set(_READS),
}


def role_has_permission(role: Role, permission: Permission) -> bool:
    """Return True if ``role`` grants ``permission``."""
    return permission in ROLE_PERMISSIONS.get(role, set())
