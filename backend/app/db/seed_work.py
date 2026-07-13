"""Seed data for the AI Work Management engine (Sprint 07).

Creates PROJECT-001 (WORLD) with milestones, three sprints, sample work items
across statuses, assignments to AI employees, and an activity timeline.
Idempotent (skips when a project already exists).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.domain.work_enums import (
    AssignmentRole,
    DependencyType,
    MilestoneStatus,
    Priority,
    ProjectStatus,
    SprintStatus,
    WorkStatus,
)
from app.models.ai import AIEmployee
from app.models.work import (
    ActivityLog,
    Assignment,
    Comment,
    Milestone,
    Project,
    ProjectSprint,
    WorkDependency,
    WorkItem,
)

# task_code, title, status, sprint_index(0-2 or None), assignee_code, priority
TASKS = [
    ("WORLD-001", "Set up project scaffolding", WorkStatus.DONE, 0, "AI-EMP-005", Priority.HIGH),
    ("WORLD-002", "Design database schema", WorkStatus.DONE, 0, "AI-EMP-005", Priority.HIGH),
    ("WORLD-003", "Implement authentication", WorkStatus.DONE, 1, "AI-EMP-005", Priority.CRITICAL),
    ("WORLD-004", "Build dashboard UI", WorkStatus.IN_PROGRESS, 2, "AI-EMP-006", Priority.HIGH),
    ("WORLD-005", "Integrate AI models", WorkStatus.ASSIGNED, 2, "AI-EMP-007", Priority.MEDIUM),
    ("WORLD-006", "Write API tests", WorkStatus.TESTING, 2, "AI-EMP-008", Priority.MEDIUM),
    ("WORLD-007", "Set up CI/CD pipeline", WorkStatus.REVIEW, 2, "AI-EMP-009", Priority.HIGH),
    ("WORLD-008", "Security audit", WorkStatus.BLOCKED, 2, "AI-EMP-010", Priority.CRITICAL),
    ("WORLD-009", "Write user documentation", WorkStatus.BACKLOG, None, "AI-EMP-012", Priority.LOW),
    (
        "WORLD-010",
        "Design system foundations",
        WorkStatus.PLANNED,
        None,
        "AI-EMP-011",
        Priority.MEDIUM,
    ),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def seed_work(db: Session) -> bool:
    """Seed PROJECT-001 (WORLD). Returns True if seeded, False if already present."""
    if db.query(Project).count() > 0:
        return False

    emps = {e.employee_code: e for e in db.query(AIEmployee).all()}
    if not emps:  # AI org must be seeded first
        return False

    ceo = emps.get("AI-EMP-001")
    architect = emps.get("AI-EMP-003")  # Chief Architect reviews technical work

    project = Project(
        code="PROJECT-001",
        name="WORLD",
        owner_ai_employee_id=ceo.id if ceo else None,
        status=ProjectStatus.ACTIVE,
        priority=Priority.HIGH,
        repository="github.com/wes/world",
        tech_stack="Python, FastAPI, SQLAlchemy, React, TypeScript, PostgreSQL",
        version=1,
    )
    db.add(project)
    db.flush()

    milestones = [
        Milestone(
            project_id=project.id,
            name="MVP Foundation",
            description="Core platform operational",
            due_date=date(2026, 8, 15),
            status=MilestoneStatus.IN_PROGRESS,
        ),
        Milestone(
            project_id=project.id,
            name="Alpha Release",
            description="First operational release",
            due_date=date(2026, 9, 30),
            status=MilestoneStatus.PENDING,
        ),
    ]
    db.add_all(milestones)

    sprints = [
        ProjectSprint(
            project_id=project.id,
            sprint_number=1,
            goal="Foundation & scaffolding",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 14),
            status=SprintStatus.COMPLETED,
            velocity=20,
        ),
        ProjectSprint(
            project_id=project.id,
            sprint_number=2,
            goal="Authentication & core engine",
            start_date=date(2026, 7, 15),
            end_date=date(2026, 7, 28),
            status=SprintStatus.COMPLETED,
            velocity=24,
        ),
        ProjectSprint(
            project_id=project.id,
            sprint_number=3,
            goal="Dashboards & AI integration",
            start_date=date(2026, 7, 29),
            end_date=date(2026, 8, 11),
            status=SprintStatus.ACTIVE,
            velocity=0,
        ),
    ]
    db.add_all(sprints)
    db.flush()

    tasks: dict[str, WorkItem] = {}
    for code, title, status, sprint_idx, assignee_code, priority in TASKS:
        assignee = emps.get(assignee_code)
        t = WorkItem(
            task_code=code,
            title=title,
            description=f"{title} for the WORLD project.",
            acceptance_criteria="Meets the Definition of Done (reviewed, tested, documented).",
            priority=priority,
            status=status,
            estimated_hours=8.0,
            actual_hours=8.0 if status == WorkStatus.DONE else None,
            project_id=project.id,
            sprint_id=sprints[sprint_idx].id if sprint_idx is not None else None,
            milestone_id=milestones[0].id,
            assigned_ai_employee_id=assignee.id if assignee else None,
            reviewer_ai_employee_id=architect.id if architect else None,
        )
        db.add(t)
        db.flush()
        tasks[code] = t
        # Assignment record + timeline entry.
        if assignee:
            db.add(
                Assignment(
                    work_item_id=t.id,
                    ai_employee_id=assignee.id,
                    role=AssignmentRole.ASSIGNEE,
                    assigned_by="AI Product Manager",
                )
            )
            db.add(
                ActivityLog(
                    project_id=project.id,
                    work_item_id=t.id,
                    actor="AI Product Manager",
                    action="task.assigned",
                    detail=f"assignee: {assignee.name}",
                )
            )

    # A dependency and a comment for realism.
    db.add(
        WorkDependency(
            work_item_id=tasks["WORLD-005"].id,
            depends_on_id=tasks["WORLD-003"].id,
            type=DependencyType.BLOCKS,
        )
    )
    db.add(
        Comment(
            work_item_id=tasks["WORLD-008"].id,
            author="Security Engineer AI",
            body="Blocked pending access to the production configuration.",
        )
    )
    db.add(
        ActivityLog(
            project_id=project.id, actor="Founder", action="project.created", detail="WORLD"
        )
    )
    return True
