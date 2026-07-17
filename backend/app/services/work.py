"""AI Work Management services — projects, sprints, tasks, assignments, activity.

Reuses the repository layer and the AI Company Core (AI employees are the
assignees/reviewers). Records an activity timeline on key events.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.work_enums import AssignmentRole, WorkStatus
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
from app.repositories.ai import AIEmployeeRepository
from app.repositories.work import (
    ActivityRepository,
    AssignmentRepository,
    CommentRepository,
    DependencyRepository,
    MilestoneRepository,
    ProjectRepository,
    SprintRepository,
    WorkItemRepository,
)
from app.schemas.work import (
    ActivityRead,
    AssignmentRead,
    CommentRead,
    DependencyRead,
    MilestoneRead,
    ProjectRead,
    SprintRead,
    WorkItemRead,
)


class WorkService:
    def __init__(self, db: Session, actor: str = "System"):
        self.db = db
        self.actor = actor
        self.projects = ProjectRepository(db)
        self.milestones = MilestoneRepository(db)
        self.sprints = SprintRepository(db)
        self.tasks = WorkItemRepository(db)
        self.assignments = AssignmentRepository(db)
        self.dependencies = DependencyRepository(db)
        self.comments = CommentRepository(db)
        self.activity = ActivityRepository(db)
        self.ai_employees = AIEmployeeRepository(db)

    # -- helpers -----------------------------------------------------------

    def _log(self, action: str, *, project_id=None, work_item_id=None, detail=None) -> None:
        self.db.add(
            ActivityLog(
                project_id=project_id,
                work_item_id=work_item_id,
                actor=self.actor,
                action=action,
                detail=detail,
            )
        )

    def _emp_names(self) -> dict:
        return {e.id: e.name for e in self.ai_employees.list_active()}

    def _emp_name(self, emp_id) -> str | None:
        if emp_id is None:
            return None
        e = self.ai_employees.get(emp_id)
        return e.name if e else None

    def _task_counts_by_project(self) -> dict:
        counts: dict = {}
        for t in self.tasks.list_all():
            counts[t.project_id] = counts.get(t.project_id, 0) + 1
        return counts

    # -- projects ----------------------------------------------------------

    def _serialize_project(self, p: Project, counts: dict, emp_names: dict) -> ProjectRead:
        return ProjectRead(
            id=p.id,
            code=p.code,
            name=p.name,
            owner_ai_employee_id=p.owner_ai_employee_id,
            owner_name=emp_names.get(p.owner_ai_employee_id),
            status=p.status,
            priority=p.priority,
            repository=p.repository,
            tech_stack=p.tech_stack,
            version=p.version,
            task_count=counts.get(p.id, 0),
            business_objective=p.business_objective,
            plan_status=p.plan_status,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    def list_projects(self, *, offset=0, limit=50) -> tuple[list[ProjectRead], int]:
        items = self.projects.list_all(offset=offset, limit=limit)
        counts = self._task_counts_by_project()
        names = self._emp_names()
        return [self._serialize_project(p, counts, names) for p in items], self.projects.count()

    def get_project(self, project_id: uuid.UUID) -> ProjectRead:
        p = self.projects.get(project_id)
        if p is None:
            raise NotFoundError(f"Project {project_id} not found")
        return self._serialize_project(p, self._task_counts_by_project(), self._emp_names())

    def create_project(self, payload) -> ProjectRead:
        if self.projects.get_by_code(payload.code):
            raise ConflictError(f"Project code '{payload.code}' already exists")
        if (
            payload.owner_ai_employee_id
            and self.ai_employees.get(payload.owner_ai_employee_id) is None
        ):
            raise ValidationError("Owner AI employee does not exist")
        import json as _json

        data = payload.model_dump()
        # Intake list fields are stored as JSON text (backward compatible).
        for key in ("deliverables", "constraints", "knowledge_references", "attachments"):
            if isinstance(data.get(key), list):
                data[key] = _json.dumps(data[key])
        p = Project(**data)
        self.projects.add(p)
        self._log("project.created", project_id=p.id, detail=p.name)
        return self.get_project(p.id)

    def update_project(self, project_id: uuid.UUID, payload) -> ProjectRead:
        p = self.projects.get(project_id)
        if p is None:
            raise NotFoundError(f"Project {project_id} not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        p.version += 1
        self.db.flush()
        self._log("project.updated", project_id=p.id)
        return self.get_project(p.id)

    def delete_project(self, project_id: uuid.UUID) -> None:
        p = self.projects.get(project_id)
        if p is None:
            raise NotFoundError(f"Project {project_id} not found")
        self.projects.delete(p)

    # -- milestones --------------------------------------------------------

    def list_milestones(self, project_id: uuid.UUID) -> list[MilestoneRead]:
        return [
            MilestoneRead.model_validate(m) for m in self.milestones.list_by_project(project_id)
        ]

    def create_milestone(self, payload) -> MilestoneRead:
        if self.projects.get(payload.project_id) is None:
            raise ValidationError("Project does not exist")
        m = Milestone(**payload.model_dump())
        self.milestones.add(m)
        self._log("milestone.created", project_id=m.project_id, detail=m.name)
        return MilestoneRead.model_validate(m)

    # -- sprints -----------------------------------------------------------

    def _serialize_sprint(self, s: ProjectSprint, tasks: list[WorkItem]) -> SprintRead:
        st = [t for t in tasks if t.sprint_id == s.id]
        done = [t for t in st if t.status == WorkStatus.DONE]
        return SprintRead(
            id=s.id,
            project_id=s.project_id,
            sprint_number=s.sprint_number,
            goal=s.goal,
            start_date=s.start_date,
            end_date=s.end_date,
            status=s.status,
            velocity=s.velocity,
            task_count=len(st),
            done_count=len(done),
            created_at=s.created_at,
            updated_at=s.updated_at,
        )

    def list_sprints(self, project_id: uuid.UUID) -> list[SprintRead]:
        tasks = self.tasks.list_all()
        return [self._serialize_sprint(s, tasks) for s in self.sprints.list_by_project(project_id)]

    def create_sprint(self, payload) -> SprintRead:
        if self.projects.get(payload.project_id) is None:
            raise ValidationError("Project does not exist")
        s = ProjectSprint(**payload.model_dump())
        self.sprints.add(s)
        self._log("sprint.created", project_id=s.project_id, detail=f"Sprint {s.sprint_number}")
        return self._serialize_sprint(s, self.tasks.list_all())

    def update_sprint(self, sprint_id: uuid.UUID, payload) -> SprintRead:
        s = self.sprints.get(sprint_id)
        if s is None:
            raise NotFoundError(f"Sprint {sprint_id} not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(s, k, v)
        self.db.flush()
        return self._serialize_sprint(s, self.tasks.list_all())

    # -- tasks -------------------------------------------------------------

    def _serialize_task(
        self, t: WorkItem, *, emp_names, project_codes, sprint_numbers, milestone_names
    ) -> WorkItemRead:
        return WorkItemRead(
            id=t.id,
            task_code=t.task_code,
            title=t.title,
            description=t.description,
            acceptance_criteria=t.acceptance_criteria,
            priority=t.priority,
            status=t.status,
            estimated_hours=t.estimated_hours,
            actual_hours=t.actual_hours,
            project_id=t.project_id,
            project_code=project_codes.get(t.project_id),
            sprint_id=t.sprint_id,
            sprint_number=sprint_numbers.get(t.sprint_id),
            milestone_id=t.milestone_id,
            milestone_name=milestone_names.get(t.milestone_id),
            assigned_ai_employee_id=t.assigned_ai_employee_id,
            assigned_name=emp_names.get(t.assigned_ai_employee_id),
            reviewer_ai_employee_id=t.reviewer_ai_employee_id,
            reviewer_name=emp_names.get(t.reviewer_ai_employee_id),
            created_at=t.created_at,
            updated_at=t.updated_at,
        )

    def _task_maps(self):
        emp_names = self._emp_names()
        project_codes = {p.id: p.code for p in self.projects.list_all(limit=10_000)}
        sprint_numbers = {s.id: s.sprint_number for s in self.sprints.list_all()}
        milestone_names = {}
        for p in self.projects.list_all(limit=10_000):
            for m in self.milestones.list_by_project(p.id):
                milestone_names[m.id] = m.name
        return dict(
            emp_names=emp_names,
            project_codes=project_codes,
            sprint_numbers=sprint_numbers,
            milestone_names=milestone_names,
        )

    def list_tasks(self, *, offset=0, limit=50, **filters) -> tuple[list[WorkItemRead], int]:
        items = self.tasks.list_filtered(offset=offset, limit=limit, **filters)
        maps = self._task_maps()
        return [self._serialize_task(t, **maps) for t in items], self.tasks.count_filtered(
            **filters
        )

    def get_task(self, task_id: uuid.UUID) -> WorkItemRead:
        t = self.tasks.get(task_id)
        if t is None:
            raise NotFoundError(f"Task {task_id} not found")
        return self._serialize_task(t, **self._task_maps())

    def _validate_task_refs(self, payload) -> None:
        for field, repo, label in (
            ("sprint_id", self.sprints, "Sprint"),
            ("milestone_id", self.milestones, "Milestone"),
            ("assigned_ai_employee_id", self.ai_employees, "Assigned AI employee"),
            ("reviewer_ai_employee_id", self.ai_employees, "Reviewer AI employee"),
        ):
            val = getattr(payload, field, None)
            if val is not None and repo.get(val) is None:
                raise ValidationError(f"{label} does not exist")

    def create_task(self, payload) -> WorkItemRead:
        if self.tasks.get_by_code(payload.task_code):
            raise ConflictError(f"Task code '{payload.task_code}' already exists")
        if self.projects.get(payload.project_id) is None:
            raise ValidationError("Project does not exist")
        self._validate_task_refs(payload)
        t = WorkItem(**payload.model_dump())
        self.tasks.add(t)
        self._log("task.created", project_id=t.project_id, work_item_id=t.id, detail=t.title)
        return self.get_task(t.id)

    def update_task(self, task_id: uuid.UUID, payload) -> WorkItemRead:
        t = self.tasks.get(task_id)
        if t is None:
            raise NotFoundError(f"Task {task_id} not found")
        data = payload.model_dump(exclude_unset=True)
        self._validate_task_refs(payload)
        old_status = t.status
        for k, v in data.items():
            setattr(t, k, v)
        self.db.flush()
        if "status" in data and data["status"] != old_status:
            new = t.status.value if hasattr(t.status, "value") else t.status
            old = old_status.value if hasattr(old_status, "value") else old_status
            self._log(
                "task.status_changed",
                project_id=t.project_id,
                work_item_id=t.id,
                detail=f"{old} -> {new}",
            )
        else:
            self._log("task.updated", project_id=t.project_id, work_item_id=t.id)
        return self.get_task(t.id)

    def delete_task(self, task_id: uuid.UUID) -> None:
        t = self.tasks.get(task_id)
        if t is None:
            raise NotFoundError(f"Task {task_id} not found")
        self.tasks.delete(t)

    # -- assignments -------------------------------------------------------

    def list_assignments(self, task_id: uuid.UUID) -> list[AssignmentRead]:
        names = self._emp_names()
        out = []
        for a in self.assignments.list_by_work_item(task_id):
            out.append(
                AssignmentRead(
                    id=a.id,
                    work_item_id=a.work_item_id,
                    ai_employee_id=a.ai_employee_id,
                    ai_employee_name=names.get(a.ai_employee_id),
                    role=a.role,
                    assigned_by=a.assigned_by,
                    created_at=a.created_at,
                )
            )
        return out

    def assign_task(self, task_id: uuid.UUID, payload) -> WorkItemRead:
        t = self.tasks.get(task_id)
        if t is None:
            raise NotFoundError(f"Task {task_id} not found")
        emp = self.ai_employees.get(payload.ai_employee_id)
        if emp is None:
            raise ValidationError("AI employee does not exist")
        self.assignments.add(
            Assignment(
                work_item_id=t.id,
                ai_employee_id=emp.id,
                role=payload.role,
                assigned_by=self.actor,
            )
        )
        if payload.role == AssignmentRole.REVIEWER:
            t.reviewer_ai_employee_id = emp.id
        else:
            t.assigned_ai_employee_id = emp.id
            if t.status in (WorkStatus.BACKLOG, WorkStatus.PLANNED):
                t.status = WorkStatus.ASSIGNED
        self.db.flush()
        self._log(
            "task.assigned",
            project_id=t.project_id,
            work_item_id=t.id,
            detail=f"{payload.role.value}: {emp.name}",
        )
        return self.get_task(t.id)

    # -- dependencies / comments -------------------------------------------

    def list_dependencies(self, task_id: uuid.UUID) -> list[DependencyRead]:
        codes = {t.id: t.task_code for t in self.tasks.list_all()}
        out = []
        for d in self.dependencies.list_by_work_item(task_id):
            out.append(
                DependencyRead(
                    id=d.id,
                    work_item_id=d.work_item_id,
                    depends_on_id=d.depends_on_id,
                    depends_on_code=codes.get(d.depends_on_id),
                    type=d.type,
                )
            )
        return out

    def add_dependency(self, task_id: uuid.UUID, payload) -> DependencyRead:
        if self.tasks.get(task_id) is None:
            raise NotFoundError(f"Task {task_id} not found")
        if payload.depends_on_id == task_id:
            raise ValidationError("A task cannot depend on itself")
        if self.tasks.get(payload.depends_on_id) is None:
            raise ValidationError("Dependency target does not exist")
        d = WorkDependency(
            work_item_id=task_id, depends_on_id=payload.depends_on_id, type=payload.type
        )
        self.dependencies.add(d)
        self._log("task.dependency_added", work_item_id=task_id, detail=payload.type.value)
        return self.list_dependencies(task_id)[-1]

    def list_comments(self, task_id: uuid.UUID) -> list[CommentRead]:
        return [CommentRead.model_validate(c) for c in self.comments.list_by_work_item(task_id)]

    def add_comment(self, task_id: uuid.UUID, payload) -> CommentRead:
        if self.tasks.get(task_id) is None:
            raise NotFoundError(f"Task {task_id} not found")
        c = Comment(work_item_id=task_id, author=payload.author or self.actor, body=payload.body)
        self.comments.add(c)
        self._log("task.commented", work_item_id=task_id)
        return CommentRead.model_validate(c)

    # -- kanban ------------------------------------------------------------

    def kanban(self, *, project_id: uuid.UUID | None = None) -> list[dict]:
        from app.domain.work_enums import KANBAN_COLUMNS

        filters = {"project_id": project_id} if project_id else {}
        items = self.tasks.list_filtered(offset=0, limit=10_000, **filters)
        maps = self._task_maps()
        serialized = [self._serialize_task(t, **maps) for t in items]
        columns = []
        for col in KANBAN_COLUMNS:
            col_val = col.value
            cards = [s for s in serialized if s.status == col]
            columns.append({"status": col_val, "count": len(cards), "tasks": cards})
        return columns

    # -- activity ----------------------------------------------------------

    def list_activity(self, *, project_id=None, work_item_id=None, offset=0, limit=50):
        items = self.activity.list(
            project_id=project_id, work_item_id=work_item_id, offset=offset, limit=limit
        )
        total = self.activity.count(project_id=project_id, work_item_id=work_item_id)
        return [ActivityRead.model_validate(a) for a in items], total
