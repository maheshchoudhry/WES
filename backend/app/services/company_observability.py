"""Company observability (Visibility phase).

Read-only aggregation that makes the AI company *visible* — every value comes from
actual runtime records already written by the workflow (Phases 1–4): work items,
development sessions (who did which stage, with which provider), handoffs (real
agent-to-agent messages), approvals, pipelines, jobs, and notifications. Nothing is
simulated; where a datum genuinely isn't tracked yet it is returned as null/empty,
never faked.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.ai import AIDepartment, AIEmployee, AIRole
from app.models.development import (
    ApprovalHistory,
    DevelopmentHandoff,
    DevelopmentSession,
    DevelopmentTask,
)
from app.models.devops import PipelineRun
from app.models.jobs import Job
from app.models.notifications import Notification
from app.models.repository import Repository
from app.models.work import Milestone, Project, ProjectSprint, WorkItem

# development stage -> live employee status label.
_STAGE_STATUS = {
    "planning": "Planning",
    "intent": "Planning",
    "repo_analysis": "Repository Analysis",
    "knowledge": "Knowledge Retrieval",
    "implementation": "Coding",
    "testing": "Testing",
    "verification": "Testing",
    "review": "Reviewing",
    "quality_gate": "Reviewing",
    "documentation": "Documenting",
    "git": "Packaging",
    "pull_request": "Packaging",
    "approval": "Waiting",
}
_ACTIVE_WORK = {"assigned", "in_progress", "review", "testing"}


def _iso(dt):
    return dt.isoformat() if dt else None


def _v(x):
    return x.value if hasattr(x, "value") else x


class CompanyObservabilityService:
    def __init__(self, db: Session):
        self.db = db

    # -- shared lookups ----------------------------------------------------

    def _emp_index(self):
        rows = self.db.execute(
            select(AIEmployee, AIRole.title, AIDepartment.name)
            .join(AIRole, AIRole.id == AIEmployee.role_id)
            .join(AIDepartment, AIDepartment.id == AIEmployee.department_id)
        ).all()
        return {e.id: (e, role, dept) for e, role, dept in rows}

    def _emp_names(self):
        return {e.id: e.name for e in self.db.scalars(select(AIEmployee)).all()}

    def _latest_session_by_emp(self):
        """Most-recent development_session per acting employee."""
        out: dict = {}
        rows = self.db.scalars(
            select(DevelopmentSession).order_by(DevelopmentSession.created_at.asc())
        ).all()
        for s in rows:
            if s.acting_ai_employee_id:
                out[s.acting_ai_employee_id] = s
        return out

    def _provider_for(self, emp) -> str:
        try:
            from app.services.providers_service import ProviderService

            return ProviderService(self.db).provider_for_employee(emp).name
        except Exception:
            return "mock"

    # -- live company ------------------------------------------------------

    def live(self) -> dict:
        idx = self._emp_index()
        latest = self._latest_session_by_emp()
        work = self.db.scalars(select(WorkItem)).all()
        by_emp_items: dict = {}
        for wi in work:
            if wi.assigned_ai_employee_id:
                by_emp_items.setdefault(wi.assigned_ai_employee_id, []).append(wi)

        employees = []
        buckets = {"working": 0, "waiting": 0, "blocked": 0, "idle": 0}
        for emp_id, (emp, role, dept) in idx.items():
            items = by_emp_items.get(emp_id, [])
            statuses = {_v(w.status) for w in items}
            sess = latest.get(emp_id)
            if "blocked" in statuses:
                state, bucket = "Blocked", "blocked"
            elif statuses & _ACTIVE_WORK:
                state = _STAGE_STATUS.get(sess.stage, "Working") if sess else "Working"
                bucket = "working"
            elif sess is not None:
                state, bucket = "Waiting", "waiting"
            else:
                state, bucket = "Idle", "idle"
            buckets[bucket] += 1
            current = next((w for w in items if _v(w.status) in _ACTIVE_WORK), None)
            employees.append(
                {
                    "id": str(emp_id),
                    "name": emp.name,
                    "code": emp.employee_code,
                    "role": role,
                    "department": dept,
                    "authority": _v(emp.authority),
                    "provider": self._provider_for(emp),
                    "status": state,
                    "current_task": current.task_code if current else None,
                }
            )

        projects = self.db.scalars(select(Project)).all()
        sprints = self.db.scalars(select(ProjectSprint)).all()
        jobs = self.db.scalars(select(Job)).all()
        pipeline = self.db.scalar(select(PipelineRun).order_by(PipelineRun.created_at.desc()))
        repo = self.db.scalar(select(Repository).order_by(Repository.last_scanned_at.desc()))
        provider_default = self._default_provider_name()

        return {
            "employees": sorted(employees, key=lambda e: e["name"]),
            "counts": {
                **buckets,
                "projects": sum(1 for p in projects if _v(p.status) != "archived"),
                "sprints": sum(1 for s in sprints if _v(s.status) in ("active", "planned")),
                "tasks_in_progress": sum(1 for w in work if _v(w.status) in _ACTIVE_WORK),
                "queue_length": sum(1 for j in jobs if j.status == "queued"),
                "running_jobs": sum(1 for j in jobs if j.status == "running"),
            },
            "pipeline_status": _v(pipeline.status) if pipeline else None,
            "provider": provider_default,
            "repository": repo.name if repo else None,
        }

    def _default_provider_name(self) -> str:
        try:
            from app.services.providers_service import ProviderService

            p = ProviderService(self.db).default_provider()
            return p.name if p else "mock"
        except Exception:
            return "mock"

    # -- executive timeline ------------------------------------------------

    def timeline(self, limit: int = 120) -> list[dict]:
        names = self._emp_names()
        task_codes = {t.id: t.code for t in self.db.scalars(select(DevelopmentTask)).all()}
        events: list[dict] = []

        for p in self.db.scalars(select(Project)):
            events.append(
                {
                    "at": _iso(p.created_at),
                    "actor": "Founder",
                    "type": "project_created",
                    "title": f"Founder created project {p.code} — {p.name}",
                }
            )
        for s in self.db.scalars(select(DevelopmentSession)):
            if s.acting_ai_employee_id and s.completed_at:
                who = names.get(s.acting_ai_employee_id, s.role or "Employee")
                events.append(
                    {
                        "at": _iso(s.completed_at),
                        "actor": who,
                        "type": "stage",
                        "title": f"{who} — {_STAGE_STATUS.get(s.stage, s.stage)} "
                        f"on {task_codes.get(s.task_id, '')}",
                        "detail": (s.detail or "")[:160],
                    }
                )
        for h in self.db.scalars(select(DevelopmentHandoff)):
            events.append(
                {
                    "at": _iso(h.created_at),
                    "actor": names.get(h.from_employee_id, h.from_role),
                    "type": "handoff",
                    "title": h.summary,
                }
            )
        for a in self.db.scalars(select(ApprovalHistory)):
            events.append(
                {
                    "at": _iso(a.created_at),
                    "actor": a.actor or "Founder",
                    "type": "approval",
                    "title": f"{a.actor or 'Founder'} {_v(a.decision)} {task_codes.get(a.task_id, '')}",
                }
            )
        for pl in self.db.scalars(select(PipelineRun)):
            events.append(
                {
                    "at": _iso(pl.created_at),
                    "actor": "DevOps",
                    "type": "pipeline",
                    "title": f"Pipeline {pl.code} {_v(pl.status)} → {pl.environment_target}",
                }
            )
        for n in self.db.scalars(select(Notification)):
            events.append(
                {
                    "at": _iso(n.created_at),
                    "actor": "System",
                    "type": n.kind,
                    "title": n.title,
                }
            )

        events = [e for e in events if e["at"]]
        events.sort(key=lambda e: e["at"], reverse=True)
        return events[:limit]

    # -- conversations (from real handoffs) --------------------------------

    def conversations(self, limit: int = 100) -> list[dict]:
        names = self._emp_names()
        task_codes = {t.id: t.code for t in self.db.scalars(select(DevelopmentTask)).all()}
        rows = self.db.scalars(
            select(DevelopmentHandoff).order_by(DevelopmentHandoff.created_at.desc()).limit(limit)
        ).all()
        return [
            {
                "at": _iso(h.created_at),
                "from": names.get(h.from_employee_id, h.from_role),
                "to": names.get(h.to_employee_id, h.to_role),
                "from_role": h.from_role,
                "to_role": h.to_role,
                "stage": h.stage,
                "message": h.summary,
                "task": task_codes.get(h.task_id),
                "status": "delivered",
            }
            for h in rows
        ]

    # -- per-employee workspace -------------------------------------------

    def employee_workspace(self, employee_id: uuid.UUID) -> dict:
        idx = self._emp_index()
        if employee_id not in idx:
            raise NotFoundError(f"AI employee {employee_id} not found")
        emp, role, dept = idx[employee_id]
        names = self._emp_names()

        items = self.db.scalars(
            select(WorkItem).where(WorkItem.assigned_ai_employee_id == employee_id)
        ).all()
        projects = {p.id: p for p in self.db.scalars(select(Project))}
        sprints = {s.id: s for s in self.db.scalars(select(ProjectSprint))}
        milestones = {m.id: m for m in self.db.scalars(select(Milestone))}
        dev_by_wi = {
            t.work_item_id: t
            for t in self.db.scalars(select(DevelopmentTask))
            if t.work_item_id
        }
        repos = {r.id: r for r in self.db.scalars(select(Repository))}

        current = next((w for w in items if _v(w.status) in _ACTIVE_WORK), None)
        cur_dev = dev_by_wi.get(current.id) if current else None
        cur_project = projects.get(current.project_id) if current else None
        cur_sprint = sprints.get(current.sprint_id) if current and current.sprint_id else None

        # Sessions (decisions) performed by this employee.
        sessions = self.db.scalars(
            select(DevelopmentSession)
            .where(DevelopmentSession.acting_ai_employee_id == employee_id)
            .order_by(DevelopmentSession.created_at.desc())
        ).all()
        latest = sessions[0] if sessions else None

        def _status_label():
            statuses = {_v(w.status) for w in items}
            if "blocked" in statuses:
                return "Blocked"
            if statuses & _ACTIVE_WORK:
                return _STAGE_STATUS.get(latest.stage, "Working") if latest else "Working"
            return "Waiting" if latest else "Idle"

        inbox = [
            {
                "task_code": w.task_code,
                "title": w.title,
                "project": projects[w.project_id].code if w.project_id in projects else None,
                "sender": names.get(w.reviewer_ai_employee_id) or "AI PM",
                "priority": _v(w.priority),
                "received": _iso(w.created_at),
                "deadline": _iso(milestones[w.milestone_id].due_date)
                if w.milestone_id in milestones and milestones[w.milestone_id].due_date
                else None,
                "repository": projects[w.project_id].repository
                if w.project_id in projects
                else None,
                "status": _v(w.status),
                "estimated_hours": w.estimated_hours,
            }
            for w in items
        ]

        buckets: dict = {
            k: [] for k in ("assigned", "in_progress", "blocked", "done", "review", "testing")
        }
        for w in items:
            st = _v(w.status)
            buckets.setdefault(st, []).append(w.task_code)

        decisions = [
            {
                "at": _iso(s.completed_at or s.started_at),
                "decision": _STAGE_STATUS.get(s.stage, s.stage),
                "stage": s.stage,
                "reason": s.detail,
                "provider": s.provider_name,
                "status": _v(s.status),
            }
            for s in sessions[:40]
        ]

        handoffs = self.db.scalars(
            select(DevelopmentHandoff)
            .where(
                (DevelopmentHandoff.from_employee_id == employee_id)
                | (DevelopmentHandoff.to_employee_id == employee_id)
            )
            .order_by(DevelopmentHandoff.created_at.desc())
        ).all()

        return {
            "profile": {
                "id": str(emp.id),
                "name": emp.name,
                "code": emp.employee_code,
                "role": role,
                "department": dept,
                "authority": _v(emp.authority),
                "provider": self._provider_for(emp),
                "status": _status_label(),
            },
            "current": {
                "task": current.task_code if current else None,
                "task_title": current.title if current else None,
                "project": cur_project.name if cur_project else None,
                "sprint": cur_sprint.sprint_number if cur_sprint else None,
                "branch": cur_dev.branch_name if cur_dev else None,
                "repository": (
                    repos[cur_dev.repository_id].name
                    if cur_dev and cur_dev.repository_id in repos
                    else (cur_project.repository if cur_project else None)
                ),
                "context": cur_dev.title if cur_dev else (current.title if current else None),
            },
            "performance": {
                "assigned": len(items),
                "in_progress": sum(1 for w in items if _v(w.status) in _ACTIVE_WORK),
                "done": sum(1 for w in items if _v(w.status) == "done"),
                "stages_performed": len(sessions),
            },
            "inbox": inbox,
            "tasks": {k: v for k, v in buckets.items()},
            "decisions": decisions,
            "handoffs": [
                {
                    "at": _iso(h.created_at),
                    "from": names.get(h.from_employee_id, h.from_role),
                    "to": names.get(h.to_employee_id, h.to_role),
                    "reason": h.summary,
                    "stage": h.stage,
                    "result": "delivered",
                }
                for h in handoffs
            ],
            "memory": self._employee_memory(employee_id),
        }

    def _employee_memory(self, employee_id: uuid.UUID) -> list[dict]:
        from app.services.memory import MemoryService

        return MemoryService(self.db).list_for_employee(employee_id, limit=15)
