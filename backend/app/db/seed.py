"""Seed data for local development.

Populates the real WES organization as recorded in the Company directories
(Department-Directory / Employee-Directory): one company, six departments, and
thirteen core AI employees with their reporting hierarchy.

Idempotent: running it again when the company already exists is a no-op.

Usage (from ``backend/`` with the virtualenv active and migrations applied):

    python -m app.db.seed
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.db.seed_ai import seed_ai
from app.db.seed_execution import seed_execution
from app.db.seed_knowledge import seed_knowledge
from app.db.seed_orchestration import seed_orchestration
from app.db.seed_repository import seed_repository
from app.db.seed_work import seed_work
from app.domain.enums import AuthorityLevel, EmployeeStatus, EntityStatus
from app.domain.roles import Role
from app.models.company import Company
from app.models.department import Department
from app.models.employee import Employee
from app.services.password import PasswordService

COMPANY = {
    "name": "WORLD Engineering Studio",
    "slug": "wes",
    "company_type": "Independent AI Engineering Company",
    "purpose": "Design, manage, review, and build software projects.",
    "description": (
        "WES is an AI engineering studio that delivers software with the discipline "
        "of a professional engineering company."
    ),
}

# code -> (name, focus)
DEPARTMENTS = [
    ("DEPT-01", "Product & Design", "What to build and how it looks and feels"),
    ("DEPT-02", "Engineering", "Architecture and building the software"),
    ("DEPT-03", "AI Systems", "Building and integrating AI capabilities"),
    ("DEPT-04", "Quality & Security", "Correct, safe, reliable work"),
    ("DEPT-05", "Project Management & Operations", "Planning, tracking, delivery"),
    ("DEPT-06", "Knowledge & Documentation", "Capturing knowledge and docs"),
]

# code, full_name, dept_code (None = leadership), position, authority, reports_to_code
EMPLOYEES = [
    ("WES-EMP-001", "Studio Director", None, "Studio Director", AuthorityLevel.EXECUTIVE, None),
    (
        "WES-EMP-002",
        "Product Manager",
        "DEPT-01",
        "Product Manager",
        AuthorityLevel.LEAD,
        "WES-EMP-001",
    ),
    (
        "WES-EMP-003",
        "UX/UI Designer",
        "DEPT-01",
        "UX/UI Designer",
        AuthorityLevel.OPERATIONAL,
        "WES-EMP-002",
    ),
    (
        "WES-EMP-004",
        "Software Architect",
        "DEPT-02",
        "Software Architect",
        AuthorityLevel.LEAD,
        "WES-EMP-001",
    ),
    (
        "WES-EMP-005",
        "Frontend Engineer",
        "DEPT-02",
        "Frontend Engineer",
        AuthorityLevel.OPERATIONAL,
        "WES-EMP-004",
    ),
    (
        "WES-EMP-006",
        "Backend Engineer",
        "DEPT-02",
        "Backend Engineer",
        AuthorityLevel.OPERATIONAL,
        "WES-EMP-004",
    ),
    (
        "WES-EMP-007",
        "AI Engineer",
        "DEPT-03",
        "AI Engineer",
        AuthorityLevel.OPERATIONAL,
        "WES-EMP-004",
    ),
    (
        "WES-EMP-008",
        "Prompt Engineer",
        "DEPT-03",
        "Prompt Engineer",
        AuthorityLevel.OPERATIONAL,
        "WES-EMP-007",
    ),
    (
        "WES-EMP-009",
        "QA Engineer",
        "DEPT-04",
        "QA Engineer",
        AuthorityLevel.OPERATIONAL,
        "WES-EMP-001",
    ),
    (
        "WES-EMP-010",
        "Security Engineer",
        "DEPT-04",
        "Security Engineer",
        AuthorityLevel.OPERATIONAL,
        "WES-EMP-001",
    ),
    (
        "WES-EMP-011",
        "Project Manager",
        "DEPT-05",
        "Project Manager",
        AuthorityLevel.LEAD,
        "WES-EMP-001",
    ),
    (
        "WES-EMP-012",
        "DevOps / Automation Engineer",
        "DEPT-05",
        "DevOps / Automation Engineer",
        AuthorityLevel.OPERATIONAL,
        "WES-EMP-004",
    ),
    (
        "WES-EMP-013",
        "Technical Writer",
        "DEPT-06",
        "Technical Writer",
        AuthorityLevel.OPERATIONAL,
        "WES-EMP-011",
    ),
]


# Role assignments so each WES OS role is represented for RBAC (Sprint 04).
# Any code not listed defaults to the Employee role.
ROLE_BY_CODE: dict[str, Role] = {
    "WES-EMP-001": Role.FOUNDER,  # Studio Director — full access
    "WES-EMP-002": Role.DIRECTOR,  # Product Manager — department access
    "WES-EMP-011": Role.DIRECTOR,  # Project Manager — department access
    "WES-EMP-004": Role.DEPARTMENT_HEAD,  # Software Architect — department management
    "WES-EMP-013": Role.READ_ONLY,  # Technical Writer — read-only access
}


def _email_for(code: str) -> str:
    return f"{code.lower()}@wes.studio"


def _role_for(code: str) -> Role:
    return ROLE_BY_CODE.get(code, Role.EMPLOYEE)


def ensure_auth_credentials(db: Session) -> None:
    """Ensure every seeded employee has a role and a login password.

    Idempotent: the role is (re)applied, and a default development password is set
    only when none exists (so changed passwords are preserved). This also backfills
    existing databases after the auth migration.
    """
    passwords = PasswordService()
    default_hash = passwords.hash(get_settings().seed_default_password)
    for employee in db.query(Employee).all():
        employee.role = _role_for(employee.employee_code)
        if not employee.password_hash:
            employee.password_hash = default_hash
        if employee.is_active is None:
            employee.is_active = True
    db.flush()


def seed(db: Session) -> Company | None:
    """Seed the WES organization + auth credentials.

    Returns the company when freshly created, or None when it already existed.
    Auth credentials are (re)ensured on every call so login works on fresh and
    pre-existing databases alike.
    """
    existing = db.query(Company).filter(Company.slug == COMPANY["slug"]).one_or_none()
    if existing is not None:
        ensure_auth_credentials(db)
        seed_ai(db)
        db.flush()
        seed_work(db)
        db.flush()
        seed_execution(db)
        db.flush()
        seed_orchestration(db)
        db.flush()
        seed_knowledge(db)
        db.flush()
        seed_repository(db)
        db.commit()
        return None

    company = Company(status=EntityStatus.ACTIVE, **COMPANY)
    db.add(company)
    db.flush()

    departments: dict[str, Department] = {}
    for code, name, focus in DEPARTMENTS:
        dept = Department(
            company_id=company.id,
            code=code,
            name=name,
            focus=focus,
            status=EntityStatus.ACTIVE,
        )
        db.add(dept)
        departments[code] = dept
    db.flush()

    passwords = PasswordService()
    default_hash = passwords.hash(get_settings().seed_default_password)

    employees: dict[str, Employee] = {}
    for code, full_name, dept_code, position, authority, manager_code in EMPLOYEES:
        emp = Employee(
            company_id=company.id,
            department_id=departments[dept_code].id if dept_code else None,
            reports_to_id=employees[manager_code].id if manager_code else None,
            employee_code=code,
            full_name=full_name,
            email=_email_for(code),
            position=position,
            authority=authority,
            status=EmployeeStatus.ACTIVE,
            role=_role_for(code),
            password_hash=default_hash,
            is_active=True,
        )
        db.add(emp)
        db.flush()
        employees[code] = emp

    seed_ai(db)
    db.flush()
    seed_work(db)
    db.flush()
    seed_execution(db)
    db.flush()
    seed_orchestration(db)
    db.flush()
    seed_knowledge(db)
    db.flush()
    seed_repository(db)
    db.commit()
    return company


def main() -> None:
    db = SessionLocal()
    try:
        company = seed(db)
        if company is None:
            print("Seed skipped: WES organization already present.")
        else:
            print(
                f"Seeded '{company.name}' with {len(DEPARTMENTS)} departments "
                f"and {len(EMPLOYEES)} employees."
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
