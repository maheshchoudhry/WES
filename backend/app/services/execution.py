"""AI Execution Engine services.

Executable framework for AI employees (no LLM): workspace aggregation, execution
queue, prompt/SOP libraries, decision rules, review queue, handoffs, execution
history, and performance metrics. Reuses the AI Company Core and Work Management.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.execution_enums import ExecutionStatus, HandoffStatus, ReviewStatus
from app.models.execution import (
    SOP,
    AIWorkspace,
    ExecutionHistory,
    ExecutionQueueItem,
    PromptTemplate,
    ReviewItem,
)
from app.repositories.ai import AIEmployeeRepository
from app.repositories.execution import (
    ContextRepository,
    DecisionRuleRepository,
    HandoffRepository,
    HistoryRepository,
    PromptRepository,
    QueueRepository,
    ReviewRepository,
    SOPRepository,
    WorkspaceRepository,
)
from app.repositories.work import WorkItemRepository
from app.schemas.execution import (
    ContextRead,
    DecisionRuleRead,
    HandoffRead,
    HistoryRead,
    PromptRead,
    QueueItemRead,
    ReviewRead,
    SOPRead,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    """Normalize a possibly-naive datetime (SQLite drops tz) to aware UTC."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


class ExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.prompts = PromptRepository(db)
        self.sops = SOPRepository(db)
        self.decisions = DecisionRuleRepository(db)
        self.workspaces = WorkspaceRepository(db)
        self.queue = QueueRepository(db)
        self.history = HistoryRepository(db)
        self.reviews = ReviewRepository(db)
        self.handoffs = HandoffRepository(db)
        self.context = ContextRepository(db)
        self.employees = AIEmployeeRepository(db)
        self.work_items = WorkItemRepository(db)

    # -- name maps ---------------------------------------------------------

    def _emp_names(self) -> dict:
        return {e.id: e.name for e in self.employees.list_active()}

    def _task_codes(self) -> dict:
        return {t.id: t.task_code for t in self.work_items.list_all()}

    # -- prompt library ----------------------------------------------------

    def list_prompts(self) -> list[PromptRead]:
        return [PromptRead.model_validate(p) for p in self.prompts.list_all()]

    def get_prompt(self, prompt_id: uuid.UUID) -> PromptRead:
        p = self.prompts.get(prompt_id)
        if p is None:
            raise NotFoundError(f"Prompt {prompt_id} not found")
        return PromptRead.model_validate(p)

    def create_prompt(self, payload) -> PromptRead:
        if self.prompts.get_by_code(payload.code):
            raise ConflictError(f"Prompt code '{payload.code}' already exists")
        p = PromptTemplate(**payload.model_dump(), version=1)
        self.prompts.add(p)
        return PromptRead.model_validate(p)

    # -- SOP library -------------------------------------------------------

    def list_sops(self) -> list[SOPRead]:
        return [SOPRead.model_validate(s) for s in self.sops.list_all()]

    def get_sop(self, sop_id: uuid.UUID) -> SOPRead:
        s = self.sops.get(sop_id)
        if s is None:
            raise NotFoundError(f"SOP {sop_id} not found")
        return SOPRead.model_validate(s)

    def create_sop(self, payload) -> SOPRead:
        if self.sops.get_by_code(payload.code):
            raise ConflictError(f"SOP code '{payload.code}' already exists")
        s = SOP(**payload.model_dump(), version=1)
        self.sops.add(s)
        return SOPRead.model_validate(s)

    # -- decision rules ----------------------------------------------------

    def list_decision_rules(self, role_id: uuid.UUID | None = None) -> list[DecisionRuleRead]:
        rules = self.decisions.list_by_role(role_id) if role_id else self.decisions.list_all()
        return [DecisionRuleRead.model_validate(r) for r in rules]

    # -- execution queue ---------------------------------------------------

    def _serialize_queue(self, item, names, codes) -> QueueItemRead:
        return QueueItemRead(
            id=item.id,
            ai_employee_id=item.ai_employee_id,
            ai_employee_name=names.get(item.ai_employee_id),
            work_item_id=item.work_item_id,
            work_item_code=codes.get(item.work_item_id),
            title=item.title,
            description=item.description,
            priority=item.priority,
            status=item.status,
            position=item.position,
            sop_id=item.sop_id,
            prompt_id=item.prompt_id,
            started_at=item.started_at,
            completed_at=item.completed_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def list_queue(self, *, ai_employee_id=None, status=None) -> list[QueueItemRead]:
        items = self.queue.list_filtered(ai_employee_id=ai_employee_id, status=status)
        names, codes = self._emp_names(), self._task_codes()
        return [self._serialize_queue(i, names, codes) for i in items]

    def create_queue_item(self, payload) -> QueueItemRead:
        if self.employees.get(payload.ai_employee_id) is None:
            raise ValidationError("AI employee does not exist")
        existing = len(self.queue.list_filtered(ai_employee_id=payload.ai_employee_id))
        item = ExecutionQueueItem(
            **payload.model_dump(), status=ExecutionStatus.QUEUED, position=existing
        )
        self.queue.add(item)
        return self._serialize_queue(item, self._emp_names(), self._task_codes())

    def advance_queue(self, item_id: uuid.UUID, payload) -> QueueItemRead:
        item = self.queue.get(item_id)
        if item is None:
            raise NotFoundError(f"Queue item {item_id} not found")
        new_status = payload.status
        if new_status == ExecutionStatus.IN_PROGRESS and item.started_at is None:
            item.started_at = _now()
        if new_status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        ):
            item.completed_at = _now()
            duration = None
            if item.started_at is not None:
                duration = int((item.completed_at - _aware(item.started_at)).total_seconds())
            self.db.add(
                ExecutionHistory(
                    ai_employee_id=item.ai_employee_id,
                    work_item_id=item.work_item_id,
                    execution_queue_id=item.id,
                    action=f"queue.{new_status.value}",
                    output=payload.output,
                    status=new_status,
                    duration_seconds=duration,
                )
            )
        item.status = new_status
        self.db.flush()
        return self._serialize_queue(item, self._emp_names(), self._task_codes())

    # -- execution history -------------------------------------------------

    def _serialize_history(self, h, names) -> HistoryRead:
        return HistoryRead(
            id=h.id,
            ai_employee_id=h.ai_employee_id,
            ai_employee_name=names.get(h.ai_employee_id),
            work_item_id=h.work_item_id,
            action=h.action,
            output=h.output,
            status=h.status,
            duration_seconds=h.duration_seconds,
            created_at=h.created_at,
        )

    def list_history(self, *, ai_employee_id=None) -> list[HistoryRead]:
        items = (
            self.history.list_by_employee(ai_employee_id)
            if ai_employee_id
            else self.history.list_all()
        )
        names = self._emp_names()
        return [self._serialize_history(h, names) for h in items]

    # -- review queue ------------------------------------------------------

    def _serialize_review(self, r, names, codes) -> ReviewRead:
        return ReviewRead(
            id=r.id,
            work_item_id=r.work_item_id,
            work_item_code=codes.get(r.work_item_id),
            reviewer_ai_employee_id=r.reviewer_ai_employee_id,
            reviewer_name=names.get(r.reviewer_ai_employee_id),
            submitter_ai_employee_id=r.submitter_ai_employee_id,
            submitter_name=names.get(r.submitter_ai_employee_id),
            status=r.status,
            notes=r.notes,
            reviewed_at=r.reviewed_at,
            created_at=r.created_at,
        )

    def list_reviews(self, *, reviewer_id=None, status=None) -> list[ReviewRead]:
        items = self.reviews.list_filtered(reviewer_id=reviewer_id, status=status)
        return [self._serialize_review(r, self._emp_names(), self._task_codes()) for r in items]

    def create_review(self, payload) -> ReviewRead:
        if self.employees.get(payload.reviewer_ai_employee_id) is None:
            raise ValidationError("Reviewer AI employee does not exist")
        r = ReviewItem(**payload.model_dump(), status=ReviewStatus.PENDING)
        self.reviews.add(r)
        return self._serialize_review(r, self._emp_names(), self._task_codes())

    def decide_review(self, review_id: uuid.UUID, payload) -> ReviewRead:
        r = self.reviews.get(review_id)
        if r is None:
            raise NotFoundError(f"Review {review_id} not found")
        r.status = payload.status
        r.notes = payload.notes if payload.notes is not None else r.notes
        r.reviewed_at = _now()
        self.db.flush()
        return self._serialize_review(r, self._emp_names(), self._task_codes())

    # -- handoffs ----------------------------------------------------------

    def _serialize_handoff(self, h, names, codes) -> HandoffRead:
        return HandoffRead(
            id=h.id,
            work_item_id=h.work_item_id,
            work_item_code=codes.get(h.work_item_id),
            from_ai_employee_id=h.from_ai_employee_id,
            from_name=names.get(h.from_ai_employee_id),
            to_ai_employee_id=h.to_ai_employee_id,
            to_name=names.get(h.to_ai_employee_id),
            stage=h.stage,
            status=h.status,
            notes=h.notes,
            sequence=h.sequence,
            created_at=h.created_at,
        )

    def list_handoffs(self, *, work_item_id=None) -> list[HandoffRead]:
        items = (
            self.handoffs.list_by_work_item(work_item_id)
            if work_item_id
            else self.handoffs.list_all()
        )
        return [self._serialize_handoff(h, self._emp_names(), self._task_codes()) for h in items]

    def advance_handoff(self, handoff_id: uuid.UUID, payload) -> HandoffRead:
        h = self.handoffs.get(handoff_id)
        if h is None:
            raise NotFoundError(f"Handoff {handoff_id} not found")
        h.status = payload.status
        if payload.status == HandoffStatus.ACCEPTED:
            h.accepted_at = _now()
        elif payload.status == HandoffStatus.COMPLETED:
            h.completed_at = _now()
        self.db.flush()
        return self._serialize_handoff(h, self._emp_names(), self._task_codes())

    # -- workspace ---------------------------------------------------------

    def get_workspace(self, employee_id: uuid.UUID) -> dict:
        emp = self.employees.get(employee_id)
        if emp is None:
            raise NotFoundError(f"AI employee {employee_id} not found")
        ws = self.workspaces.get_by_employee(employee_id)
        if ws is None:
            ws = AIWorkspace(ai_employee_id=employee_id, status="active")
            self.workspaces.add(ws)

        names, codes = self._emp_names(), self._task_codes()
        queue = self.queue.list_filtered(ai_employee_id=employee_id)
        history = self.history.list_by_employee(employee_id)
        pending_reviews = self.reviews.list_filtered(
            reviewer_id=employee_id, status=ReviewStatus.PENDING
        )
        inbox = self.handoffs.list_pending_for(employee_id)
        assigned_tasks = self.work_items.list_filtered(
            assigned_ai_employee_id=employee_id, limit=100
        )

        completed = [q for q in queue if q.status == ExecutionStatus.COMPLETED]
        durations = [h.duration_seconds for h in history if h.duration_seconds is not None]
        avg_duration = round(sum(durations) / len(durations)) if durations else None

        return {
            "employee": {
                "id": str(emp.id),
                "employee_code": emp.employee_code,
                "name": emp.name,
                "role": emp.role.title if emp.role else None,
                "department": emp.department.name if emp.department else None,
            },
            "context": ws.context,
            "inbox": [self._serialize_handoff(h, names, codes).model_dump() for h in inbox],
            "assigned_tasks": [
                {
                    "id": str(t.id),
                    "task_code": t.task_code,
                    "title": t.title,
                    "status": t.status.value if hasattr(t.status, "value") else t.status,
                    "priority": t.priority.value if hasattr(t.priority, "value") else t.priority,
                }
                for t in assigned_tasks
            ],
            "queue": [self._serialize_queue(q, names, codes).model_dump() for q in queue],
            "review_queue": [
                self._serialize_review(r, names, codes).model_dump() for r in pending_reviews
            ],
            "history": [self._serialize_history(h, names).model_dump() for h in history[:10]],
            "context_items": [
                {"key": c.key, "value": c.value} for c in self.context.list_by_employee(employee_id)
            ],
            "kpis": [{"name": k.name, "target": k.target, "unit": k.unit} for k in emp.kpis],
            "performance": {
                "queued": sum(1 for q in queue if q.status == ExecutionStatus.QUEUED),
                "in_progress": sum(1 for q in queue if q.status == ExecutionStatus.IN_PROGRESS),
                "completed": len(completed),
                "pending_reviews": len(pending_reviews),
                "avg_duration_seconds": avg_duration,
            },
        }

    def list_context(self, employee_id: uuid.UUID) -> list[ContextRead]:
        return [ContextRead.model_validate(c) for c in self.context.list_by_employee(employee_id)]

    # -- dashboards / performance -----------------------------------------

    def founder_dashboard(self) -> dict:
        queue = self.queue.list_all()
        reviews = self.reviews.list_all()
        history = self.history.list_all()
        durations = [h.duration_seconds for h in history if h.duration_seconds is not None]
        return {
            "ai_work_queue": len(queue),
            "queued": sum(1 for q in queue if q.status == ExecutionStatus.QUEUED),
            "in_progress": sum(1 for q in queue if q.status == ExecutionStatus.IN_PROGRESS),
            "pending_reviews": sum(1 for r in reviews if r.status == ReviewStatus.PENDING),
            "completed_work": sum(1 for q in queue if q.status == ExecutionStatus.COMPLETED),
            "avg_completion_seconds": round(sum(durations) / len(durations)) if durations else None,
            "organization_performance": {
                "total_executions": len(history),
                "handoffs": len(self.handoffs.list_all()),
            },
        }

    def ai_dashboard(self) -> dict:
        queue = self.queue.list_all()
        reviews = self.reviews.list_all()
        history = self.history.list_all()
        by_employee: dict = {}
        names = self._emp_names()
        for q in queue:
            name = names.get(q.ai_employee_id, "Unknown")
            by_employee[name] = by_employee.get(name, 0) + 1
        return {
            "inbox": len(self.handoffs.list_all()),
            "current_work": sum(1 for q in queue if q.status == ExecutionStatus.IN_PROGRESS),
            "execution_queue": len(queue),
            "review_queue": sum(1 for r in reviews if r.status == ReviewStatus.PENDING),
            "history": len(history),
            "work_by_employee": by_employee,
        }
