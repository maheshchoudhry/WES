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
    # Execution Engine (Sprint 08)
    EXEC_READ = "exec:read"
    EXEC_WRITE = "exec:write"  # queue advance, reviews, handoffs, library authoring
    # Orchestration Engine (Sprint 09)
    ORCH_READ = "orch:read"
    ORCH_WRITE = "orch:write"  # run pipeline, provider settings (Founder only)
    # Organizational Knowledge Engine (Sprint 10)
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"  # author / edit documents (authors + management)
    KNOWLEDGE_APPROVE = "knowledge:approve"  # approve / reject reviews (Directors + Founder)


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
    Permission.EXEC_READ,
    Permission.ORCH_READ,
    Permission.KNOWLEDGE_READ,
}

ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    # Full access to everything.
    Role.FOUNDER: set(Permission),
    # Project management: manages departments, employees, AI org, work, execution.
    Role.DIRECTOR: _READS
    | {
        Permission.DEPARTMENT_WRITE,
        Permission.EMPLOYEE_WRITE,
        Permission.AI_UPDATE,
        Permission.WORK_WRITE,
        Permission.EXEC_WRITE,
        # Knowledge: authors documents and approves reviews.
        Permission.KNOWLEDGE_WRITE,
        Permission.KNOWLEDGE_APPROVE,
    },
    # Department management: manages employees, AI org, department work, execution.
    Role.DEPARTMENT_HEAD: _READS
    | {
        Permission.EMPLOYEE_WRITE,
        Permission.AI_UPDATE,
        Permission.WORK_WRITE,
        Permission.EXEC_WRITE,
        # Knowledge: authors documents (Technical Writer / content authoring).
        Permission.KNOWLEDGE_WRITE,
    },
    # Self workspace: read-only across the workspace (view assigned work).
    Role.EMPLOYEE: set(_READS),
    # Read-only access.
    Role.READ_ONLY: set(_READS),
}


def role_has_permission(role: Role, permission: Permission) -> bool:
    """Return True if ``role`` grants ``permission``."""
    return permission in ROLE_PERMISSIONS.get(role, set())
