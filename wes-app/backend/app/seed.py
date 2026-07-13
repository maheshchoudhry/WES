"""Seed the WES database with the core company, departments, and employees.

Idempotent: does nothing if a company already exists. Run with:
    python -m app.seed
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Company, Department, Employee

DEPARTMENTS = [
    ("PROD", "Product & Design", "What to build and how it looks and feels"),
    ("ENG", "Engineering", "Architecture and building the software"),
    ("AI", "AI Systems", "Building and integrating AI capabilities"),
    ("QS", "Quality & Security", "Correct, safe, and reliable work"),
    ("PMO", "Project Management & Operations", "Planning, tracking, and delivery"),
    ("KD", "Knowledge & Documentation", "Capturing knowledge and documentation"),
]

EMPLOYEES = [
    ("WES-EMP-001", "Studio Director", "Studio Director", None, "Founder / Owner", "Executive"),
    ("WES-EMP-002", "Product Manager", "Product Manager", "PROD", "Studio Director", "Lead"),
    ("WES-EMP-003", "UX/UI Designer", "UX/UI Designer", "PROD", "Product Manager", "Operational"),
    ("WES-EMP-004", "Software Architect", "Software Architect", "ENG", "Studio Director", "Lead"),
    ("WES-EMP-005", "Frontend Engineer", "Frontend Engineer", "ENG", "Software Architect", "Operational"),
    ("WES-EMP-006", "Backend Engineer", "Backend Engineer", "ENG", "Software Architect", "Operational"),
    ("WES-EMP-007", "AI Engineer", "AI Engineer", "AI", "Software Architect", "Operational"),
    ("WES-EMP-008", "Prompt Engineer", "Prompt Engineer", "AI", "AI Engineer", "Operational"),
    ("WES-EMP-009", "QA Engineer", "QA Engineer", "QS", "Studio Director", "Operational"),
    ("WES-EMP-010", "Security Engineer", "Security Engineer", "QS", "Studio Director", "Operational"),
    ("WES-EMP-011", "Project Manager", "Project Manager", "PMO", "Studio Director", "Lead"),
    ("WES-EMP-012", "DevOps / Automation Engineer", "DevOps / Automation Engineer", "PMO", "Software Architect", "Operational"),
    ("WES-EMP-013", "Technical Writer", "Technical Writer", "KD", "Project Manager", "Operational"),
]


def run() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(Company)) is not None:
            print("Seed skipped: data already present.")
            return

        db.add(
            Company(
                name="WORLD Engineering Studio",
                legal_type="AI Engineering Company",
                mission="Design, manage, review, and build software projects.",
            )
        )

        dept_ids: dict[str, int] = {}
        for code, name, focus in DEPARTMENTS:
            dept = Department(code=code, name=name, focus=focus)
            db.add(dept)
            db.flush()
            dept_ids[code] = dept.id

        for code, name, position, dept_code, reports_to, authority in EMPLOYEES:
            db.add(
                Employee(
                    employee_code=code,
                    name=name,
                    position=position,
                    department_id=dept_ids[dept_code] if dept_code else None,
                    reports_to=reports_to,
                    authority_level=authority,
                )
            )

        db.commit()
        print(
            f"Seed complete: 1 company, {len(DEPARTMENTS)} departments, "
            f"{len(EMPLOYEES)} employees."
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
