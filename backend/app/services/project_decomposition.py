"""Autonomous Project Decomposition (WP6, Phase 1).

Turns a Founder Project Intake (a business objective + deliverables + constraints)
into a real, reviewable plan built entirely from the EXISTING work schema:

    Intake -> Business Analysis (AI CEO) -> Epics (milestones) ->
    Sprints (project_sprints) -> Tasks (work_items) -> AI-employee assignment

The plan is produced in a ``decomposed`` state and MUST be Founder-approved before
any execution begins — decomposition never starts implementation (project.status
stays PLANNING). Assignment maps each task to a REAL seeded ``ai_employees`` row by
role, so tasks carry a genuine assignee (the bridge to WP7 collaboration).

Analysis and task shaping are deterministic today (no LLM), and provider-pluggable:
when a live provider is configured (WP2), ``_analyze`` / ``_shape_tasks`` can delegate
without changing this contract or the schema.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.ai_enums import AIDecisionAuthority
from app.domain.work_enums import (
    MilestoneStatus,
    Priority,
    ProjectStatus,
    SprintStatus,
    WorkStatus,
)
from app.models.ai import AIEmployee, AIRole
from app.models.work import Milestone, Project, ProjectSprint, WorkItem

# Per-epic task blueprint: (label suffix, role keyword, estimated hours).
_TASK_TEMPLATE = [
    ("Design & architecture", "architect", 4.0),
    ("Backend implementation", "backend", 12.0),
    ("Frontend integration", "frontend", 8.0),
    ("Tests & QA", "qa", 6.0),
    ("Documentation", "writer", 3.0),
]


def _loads(v: str | None) -> list:
    if not v:
        return []
    try:
        data = json.loads(v)
        return data if isinstance(data, list) else [data]
    except (ValueError, TypeError):
        return [v]


class DecompositionService:
    def __init__(self, db: Session):
        self.db = db

    # -- AI employee lookup ------------------------------------------------

    def _employees_by_role(self) -> list[tuple[str, AIEmployee]]:
        rows = self.db.execute(
            select(AIRole.title, AIEmployee)
            .join(AIEmployee, AIEmployee.role_id == AIRole.id)
            .where(AIEmployee.is_deleted.is_(False))
        ).all()
        return [(t.lower(), e) for t, e in rows]

    def _find_employee(self, keyword: str) -> AIEmployee | None:
        pairs = self._employees_by_role()
        for title, emp in pairs:
            if keyword in title:
                return emp
        return None

    def _ceo(self) -> AIEmployee | None:
        # The executive with no manager is the AI CEO (business rule in the AI org).
        emp = self.db.scalar(
            select(AIEmployee)
            .where(
                AIEmployee.authority == AIDecisionAuthority.EXECUTIVE,
                AIEmployee.manager_id.is_(None),
                AIEmployee.is_deleted.is_(False),
            )
            .limit(1)
        )
        return emp or self.db.scalar(select(AIEmployee).limit(1))

    # -- business analysis (AI CEO) ---------------------------------------

    def _analyze(self, project: Project) -> dict:
        objective = project.business_objective or project.name
        deliverables = _loads(project.deliverables)
        constraints = _loads(project.constraints)
        ceo = self._ceo()
        return {
            "analyst": ceo.name if ceo else "AI CEO",
            "vision": f"Deliver '{objective}' as a production-quality capability within WES OS.",
            "scope": {
                "in_scope": deliverables or [objective],
                "out_of_scope": ["Anything outside the stated deliverables and repository."],
            },
            "risks": (
                [f"Constraint: {c}" for c in constraints]
                + [
                    "Integration risk with existing modules.",
                    "Effort/timeline uncertainty until tasks are estimated.",
                ]
            ),
            "architecture_proposal": (
                f"Extend the existing layered architecture (API -> Service -> Repository -> ORM)"
                f"{' in ' + project.repository if project.repository else ''}. "
                "Reuse Quality Gates, Repository Intelligence, and the Knowledge Engine; "
                "no schema or API rewrites."
            ),
        }

    # -- epics / sprints / tasks ------------------------------------------

    def _epic_names(self, project: Project) -> list[str]:
        deliverables = _loads(project.deliverables)
        if deliverables:
            return [str(d)[:180] for d in deliverables]
        # No explicit deliverables -> a standard lifecycle breakdown.
        return ["Foundation", "Core Implementation", "Quality & Hardening", "Release"]

    def _next_task_index(self, project: Project) -> int:
        n = (
            self.db.scalar(
                select(func.count(WorkItem.id)).where(WorkItem.project_id == project.id)
            )
            or 0
        )
        return n + 1

    def decompose(self, project_id: uuid.UUID) -> dict:
        project = self.db.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        if project.plan_status == "approved":
            raise ValidationError("Project plan is already approved; decomposition is locked.")

        # Clear any prior (unapproved) decomposition so re-running is idempotent.
        for m in self.db.scalars(
            select(Milestone).where(Milestone.project_id == project.id)
        ).all():
            self.db.delete(m)
        for s in self.db.scalars(
            select(ProjectSprint).where(ProjectSprint.project_id == project.id)
        ).all():
            self.db.delete(s)
        for t in self.db.scalars(
            select(WorkItem).where(WorkItem.project_id == project.id)
        ).all():
            self.db.delete(t)
        self.db.flush()

        analysis = self._analyze(project)
        project.business_analysis = json.dumps(analysis)

        epics = self._epic_names(project)
        priority = project.priority if isinstance(project.priority, Priority) else Priority.MEDIUM
        task_idx = self._next_task_index(project)
        created_epics: list[dict] = []

        for e_i, epic_name in enumerate(epics, start=1):
            milestone = Milestone(
                project_id=project.id,
                name=epic_name,
                description=f"Epic {e_i}: {epic_name}",
                status=MilestoneStatus.PENDING,
            )
            self.db.add(milestone)
            self.db.flush()

            sprint = ProjectSprint(
                project_id=project.id,
                sprint_number=e_i,
                goal=f"Deliver epic: {epic_name}",
                status=SprintStatus.PLANNED,
            )
            self.db.add(sprint)
            self.db.flush()

            epic_tasks: list[dict] = []
            for suffix, role_kw, hours in _TASK_TEMPLATE:
                emp = self._find_employee(role_kw)
                reviewer = self._find_employee("architect") or self._ceo()
                task = WorkItem(
                    task_code=f"{project.code}-T{task_idx:03d}",
                    title=f"{suffix} — {epic_name}",
                    description=f"{suffix} for epic '{epic_name}'.",
                    acceptance_criteria=(project.acceptance_criteria or None),
                    priority=priority,
                    status=WorkStatus.BACKLOG,
                    estimated_hours=hours,
                    project_id=project.id,
                    sprint_id=sprint.id,
                    milestone_id=milestone.id,
                    assigned_ai_employee_id=emp.id if emp else None,
                    reviewer_ai_employee_id=reviewer.id if reviewer else None,
                )
                self.db.add(task)
                self.db.flush()
                task_idx += 1
                epic_tasks.append(
                    {
                        "task_code": task.task_code,
                        "title": task.title,
                        "role": role_kw,
                        "assignee": emp.name if emp else None,
                        "estimated_hours": hours,
                    }
                )

            created_epics.append(
                {
                    "epic": epic_name,
                    "sprint_number": sprint.sprint_number,
                    "tasks": epic_tasks,
                }
            )

        # Decomposed, awaiting Founder approval. Implementation does NOT start.
        project.plan_status = "decomposed"
        project.status = ProjectStatus.PLANNING
        self.db.flush()

        return self.plan(project.id)

    def approve_plan(self, project_id: uuid.UUID, approved_by: str = "Founder") -> dict:
        project = self.db.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        if project.plan_status != "decomposed":
            raise ValidationError(
                f"Project has no decomposed plan to approve (plan_status={project.plan_status})."
            )
        project.plan_status = "approved"
        self.db.flush()
        # Phase 4: Founder approval kicks off autonomous execution — enqueue a
        # durable project-execution job (turns tasks into dev workflows).
        from app.services.job_queue import JobQueue

        JobQueue(self.db).enqueue(
            "project_execution",
            {"project_id": str(project.id)},
            idempotency_key=f"project-exec:{project.id}",
        )
        return self.plan(project.id)

    def plan(self, project_id: uuid.UUID) -> dict:
        project = self.db.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        milestones = self.db.scalars(
            select(Milestone).where(Milestone.project_id == project.id).order_by(Milestone.name)
        ).all()
        sprints = self.db.scalars(
            select(ProjectSprint)
            .where(ProjectSprint.project_id == project.id)
            .order_by(ProjectSprint.sprint_number)
        ).all()
        tasks = self.db.scalars(
            select(WorkItem).where(WorkItem.project_id == project.id).order_by(WorkItem.task_code)
        ).all()
        emp_names = {
            e.id: e.name for e in self.db.scalars(select(AIEmployee)).all()
        }
        return {
            "project": {
                "id": str(project.id),
                "code": project.code,
                "name": project.name,
                "business_objective": project.business_objective,
                "plan_status": project.plan_status,
                "status": project.status.value
                if hasattr(project.status, "value")
                else project.status,
            },
            "business_analysis": json.loads(project.business_analysis)
            if project.business_analysis
            else None,
            "epics": [{"id": str(m.id), "name": m.name, "status": _v(m.status)} for m in milestones],
            "sprints": [
                {"sprint_number": s.sprint_number, "goal": s.goal, "status": _v(s.status)}
                for s in sprints
            ],
            "tasks": [
                {
                    "task_code": t.task_code,
                    "title": t.title,
                    "sprint_id": str(t.sprint_id) if t.sprint_id else None,
                    "milestone_id": str(t.milestone_id) if t.milestone_id else None,
                    "assignee": emp_names.get(t.assigned_ai_employee_id),
                    "reviewer": emp_names.get(t.reviewer_ai_employee_id),
                    "estimated_hours": t.estimated_hours,
                    "status": _v(t.status),
                }
                for t in tasks
            ],
            "totals": {
                "epics": len(milestones),
                "sprints": len(sprints),
                "tasks": len(tasks),
                "estimated_hours": sum(t.estimated_hours or 0 for t in tasks),
            },
        }


def _v(x) -> str:
    return x.value if hasattr(x, "value") else x
