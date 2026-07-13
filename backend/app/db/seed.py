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

from app.core.database import SessionLocal
from app.domain.enums import AuthorityLevel, EmployeeStatus, EntityStatus
from app.models.company import Company
from app.models.department import Department
from app.models.employee import Employee

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
    ("WES-EMP-002", "Product Manager", "DEPT-01", "Product Manager", AuthorityLevel.LEAD, "WES-EMP-001"),
    ("WES-EMP-003", "UX/UI Designer", "DEPT-01", "UX/UI Designer", AuthorityLevel.OPERATIONAL, "WES-EMP-002"),
    ("WES-EMP-004", "Software Architect", "DEPT-02", "Software Architect", AuthorityLevel.LEAD, "WES-EMP-001"),
    ("WES-EMP-005", "Frontend Engineer", "DEPT-02", "Frontend Engineer", AuthorityLevel.OPERATIONAL, "WES-EMP-004"),
    ("WES-EMP-006", "Backend Engineer", "DEPT-02", "Backend Engineer", AuthorityLevel.OPERATIONAL, "WES-EMP-004"),
    ("WES-EMP-007", "AI Engineer", "DEPT-03", "AI Engineer", AuthorityLevel.OPERATIONAL, "WES-EMP-004"),
    ("WES-EMP-008", "Prompt Engineer", "DEPT-03", "Prompt Engineer", AuthorityLevel.OPERATIONAL, "WES-EMP-007"),
    ("WES-EMP-009", "QA Engineer", "DEPT-04", "QA Engineer", AuthorityLevel.OPERATIONAL, "WES-EMP-001"),
    ("WES-EMP-010", "Security Engineer", "DEPT-04", "Security Engineer", AuthorityLevel.OPERATIONAL, "WES-EMP-001"),
    ("WES-EMP-011", "Project Manager", "DEPT-05", "Project Manager", AuthorityLevel.LEAD, "WES-EMP-001"),
    ("WES-EMP-012", "DevOps / Automation Engineer", "DEPT-05", "DevOps / Automation Engineer", AuthorityLevel.OPERATIONAL, "WES-EMP-004"),
    ("WES-EMP-013", "Technical Writer", "DEPT-06", "Technical Writer", AuthorityLevel.OPERATIONAL, "WES-EMP-011"),
]


def _email_for(code: str) -> str:
    return f"{code.lower()}@wes.studio"


def seed(db: Session) -> Company | None:
    """Seed the WES organization. Returns the company, or None if already seeded."""
    existing = db.query(Company).filter(Company.slug == COMPANY["slug"]).one_or_none()
    if existing is not None:
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
        )
        db.add(emp)
        db.flush()
        employees[code] = emp

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
