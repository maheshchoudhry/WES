"""Work analytics for the Founder and AI Company dashboards."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.work_enums import WorkStatus
from app.repositories.ai import AIDepartmentRepository, AIEmployeeRepository
from app.repositories.work import (
    MilestoneRepository,
    ProjectRepository,
    SprintRepository,
    WorkItemRepository,
)

_OPEN = {
    WorkStatus.ASSIGNED,
    WorkStatus.IN_PROGRESS,
    WorkStatus.REVIEW,
    WorkStatus.TESTING,
    WorkStatus.BLOCKED,
}


def _val(x) -> str:
    return x.value if hasattr(x, "value") else x


class WorkAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.projects = ProjectRepository(db)
        self.sprints = SprintRepository(db)
        self.tasks = WorkItemRepository(db)
        self.milestones = MilestoneRepository(db)
        self.ai_employees = AIEmployeeRepository(db)
        self.ai_departments = AIDepartmentRepository(db)

    def founder_summary(self) -> dict:
        tasks = self.tasks.list_all()
        projects = self.projects.list_all(limit=10_000)
        sprints = self.sprints.list_all()

        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        for t in tasks:
            by_status[_val(t.status)] = by_status.get(_val(t.status), 0) + 1
            by_priority[_val(t.priority)] = by_priority.get(_val(t.priority), 0) + 1

        blocked = [t for t in tasks if t.status == WorkStatus.BLOCKED]

        # Sprint progress for active sprints.
        sprint_progress = []
        for s in sprints:
            st = [t for t in tasks if t.sprint_id == s.id]
            done = [t for t in st if t.status == WorkStatus.DONE]
            sprint_progress.append(
                {
                    "sprint_number": s.sprint_number,
                    "status": _val(s.status),
                    "total": len(st),
                    "done": len(done),
                    "velocity": s.velocity,
                }
            )
        velocity = sum(s.velocity for s in sprints if _val(s.status) == "completed")

        # Upcoming milestone deadlines.
        upcoming = []
        for p in projects:
            for m in self.milestones.list_by_project(p.id):
                if m.due_date and _val(m.status) != "completed":
                    upcoming.append(
                        {
                            "name": m.name,
                            "due_date": m.due_date.isoformat(),
                            "status": _val(m.status),
                        }
                    )
        upcoming.sort(key=lambda x: x["due_date"])

        # AI workload: open tasks per assignee.
        names = {e.id: e.name for e in self.ai_employees.list_active()}
        workload: dict[str, int] = {}
        for t in tasks:
            if t.assigned_ai_employee_id and t.status in _OPEN:
                name = names.get(t.assigned_ai_employee_id, "Unknown")
                workload[name] = workload.get(name, 0) + 1

        return {
            "total_projects": len(projects),
            "total_tasks": len(tasks),
            "tasks_by_status": by_status,
            "tasks_by_priority": by_priority,
            "blocked_tasks": len(blocked),
            "sprint_progress": sprint_progress,
            "velocity": velocity,
            "upcoming_deadlines": upcoming[:5],
            "ai_workload": workload,
        }

    def ai_summary(self) -> dict:
        tasks = self.tasks.list_all()
        employees = self.ai_employees.list_active()
        names = {e.id: e.name for e in employees}
        dept_names = {d.id: d.name for d in self.ai_departments.list_all()}
        emp_dept = {e.id: dept_names.get(e.department_id, "Unknown") for e in employees}

        assigned = sum(1 for t in tasks if t.assigned_ai_employee_id and t.status in _OPEN)
        in_progress = sum(1 for t in tasks if t.status == WorkStatus.IN_PROGRESS)
        completed = sum(1 for t in tasks if t.status == WorkStatus.DONE)

        distribution: dict[str, int] = {}
        department_load: dict[str, int] = {}
        for t in tasks:
            if t.assigned_ai_employee_id and t.status in _OPEN:
                distribution[names.get(t.assigned_ai_employee_id, "Unknown")] = (
                    distribution.get(names.get(t.assigned_ai_employee_id, "Unknown"), 0) + 1
                )
                dept = emp_dept.get(t.assigned_ai_employee_id, "Unknown")
                department_load[dept] = department_load.get(dept, 0) + 1

        team_size = len(employees)
        return {
            "assigned_work": assigned,
            "current_tasks": in_progress,
            "completed_work": completed,
            "team_capacity": {
                "team_size": team_size,
                "open_tasks": assigned,
                "avg_load": round(assigned / team_size, 2) if team_size else 0,
            },
            "work_distribution": distribution,
            "department_load": department_load,
        }
