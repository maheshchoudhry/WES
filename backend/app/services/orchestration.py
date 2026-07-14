"""AI Orchestration Engine.

Runs the provider-independent execution pipeline:

    Queue -> Context -> Prompt -> Provider -> Response -> Review -> History -> Next

Business logic never references a concrete provider — only the Provider
Abstraction Layer (via ProviderService / ProviderFactory).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.orchestration_enums import MessageRole, ReviewOutcome, RunStatus
from app.models.ai import AIEmployee
from app.models.execution import SOP, DecisionRule, Handoff, PromptTemplate
from app.models.orchestration import (
    ConversationThread,
    CostTracking,
    ExecutionMessage,
    ExecutionMetric,
    ExecutionRun,
    ProviderHealthRecord,
    RetryHistory,
    TokenUsage,
)
from app.models.work import Project, ProjectSprint, WorkItem
from app.providers import ExecutionRequest, Message, ProviderError
from app.services.providers_service import ProviderService

PROMPT_VERSION = "v1"
MAX_ATTEMPTS = 2


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- Context builder ----------------------------------------------------
class ContextBuilder:
    def __init__(self, db: Session):
        self.db = db

    def build(self, employee: AIEmployee, work_item: WorkItem | None) -> dict:
        project = sprint = None
        if work_item is not None:
            project = self.db.get(Project, work_item.project_id)
            if work_item.sprint_id:
                sprint = self.db.get(ProjectSprint, work_item.sprint_id)
        sop = self.db.scalar(select(SOP).where(SOP.code == "SOP-CODE"))
        prompt = self.db.scalar(select(PromptTemplate).where(PromptTemplate.code == "PROMPT-TASK"))
        rules = (
            list(
                self.db.scalars(
                    select(DecisionRule).where(DecisionRule.ai_role_id == employee.role_id)
                ).all()
            )
            if employee.role_id
            else []
        )
        return {
            "project": (
                {
                    "code": project.code,
                    "name": project.name,
                    "repository": project.repository,
                    "tech_stack": project.tech_stack,
                }
                if project
                else None
            ),
            "sprint": {"number": sprint.sprint_number, "goal": sprint.goal} if sprint else None,
            "task": (
                {
                    "code": work_item.task_code,
                    "title": work_item.title,
                    "acceptance_criteria": work_item.acceptance_criteria,
                }
                if work_item
                else None
            ),
            "employee": {
                "name": employee.name,
                "role": employee.role.title if employee.role else None,
                "department": employee.department.name if employee.department else None,
                "responsibilities": [r.description for r in employee.responsibilities],
                "capabilities": [c.name for c in employee.capabilities],
                "decision_scope": employee.decision_scope,
            },
            "sop": {"title": sop.title, "content": sop.content} if sop else None,
            "prompt": {"code": prompt.code, "content": prompt.content} if prompt else None,
            "decision_rules": [
                {
                    "type": r.rule_type.value if hasattr(r.rule_type, "value") else r.rule_type,
                    "name": r.name,
                }
                for r in rules
            ],
            "organization": "WORLD Engineering Studio — AI software company.",
        }


# --- Prompt builder -----------------------------------------------------
class PromptBuilder:
    version = PROMPT_VERSION

    def build(
        self, context: dict, previous: list[Message] | None = None
    ) -> tuple[list[Message], str]:
        emp = context["employee"]
        messages: list[Message] = [
            Message(
                role="system",
                content=f"You are {emp['name']}, {emp['role']} at {context['organization']} Follow the SOP and decision rules.",
            ),
            Message(
                role="system",
                content=(
                    "Responsibilities: " + "; ".join(emp["responsibilities"])
                    if emp["responsibilities"]
                    else "Responsibilities: role-defined."
                ),
            ),
        ]
        if context.get("sop"):
            messages.append(
                Message(
                    role="system",
                    content=f"SOP — {context['sop']['title']}: {context['sop']['content']}",
                )
            )
        task = context.get("task")
        if task:
            messages.append(
                Message(
                    role="user",
                    content=(
                        f"Task {task['code']}: {task['title']}. "
                        f"Acceptance criteria: {task.get('acceptance_criteria') or 'meet the Definition of Done'}. "
                        f"Repository: {(context.get('project') or {}).get('repository', 'n/a')}. "
                        "Produce your output and prepare for review."
                    ),
                )
            )
        else:
            messages.append(
                Message(
                    role="user", content="Perform your assigned duties for the current project."
                )
            )
        for m in previous or []:
            messages.append(m)
        return messages, self.version


# --- Memory -------------------------------------------------------------
class LongTermMemory(ABC):
    """Interface for a future long-term/vector memory backend."""

    @abstractmethod
    def remember(self, key: str, value: str) -> None: ...

    @abstractmethod
    def recall(self, query: str) -> list[str]: ...


class NullLongTermMemory(LongTermMemory):
    def remember(self, key: str, value: str) -> None:  # no-op until a backend exists
        return None

    def recall(self, query: str) -> list[str]:
        return []


class MemoryService:
    def __init__(self, db: Session):
        self.db = db
        self.long_term: LongTermMemory = NullLongTermMemory()

    def short_term(self, thread_id: uuid.UUID, limit: int = 10) -> list[ExecutionMessage]:
        rows = self.db.scalars(
            select(ExecutionMessage)
            .where(ExecutionMessage.thread_id == thread_id)
            .order_by(ExecutionMessage.sequence.desc())
            .limit(limit)
        ).all()
        return list(reversed(rows))

    def conversation(self, thread_id: uuid.UUID) -> list[ExecutionMessage]:
        return list(
            self.db.scalars(
                select(ExecutionMessage)
                .where(ExecutionMessage.thread_id == thread_id)
                .order_by(ExecutionMessage.sequence)
            ).all()
        )


# --- Orchestration service (pipeline + orchestrator + review) -----------
class OrchestrationService:
    def __init__(self, db: Session, actor: str = "System"):
        self.db = db
        self.actor = actor
        self.providers = ProviderService(db)
        self.context_builder = ContextBuilder(db)
        self.prompt_builder = PromptBuilder()
        self.memory = MemoryService(db)

    def _emp_names(self) -> dict:
        return {e.id: e.name for e in self.db.scalars(select(AIEmployee)).all()}

    def _provider_names(self) -> dict:
        return {p.id: p.name for p in self.providers.list_providers()}

    def serialize_run(self, run: ExecutionRun) -> dict:
        return {
            "id": str(run.id),
            "thread_id": str(run.thread_id) if run.thread_id else None,
            "ai_employee_id": str(run.ai_employee_id) if run.ai_employee_id else None,
            "ai_employee_name": self._emp_names().get(run.ai_employee_id),
            "provider_id": str(run.provider_id),
            "provider_name": self._provider_names().get(run.provider_id),
            "model": run.model,
            "prompt_version": run.prompt_version,
            "status": run.status.value if hasattr(run.status, "value") else run.status,
            "input_summary": run.input_summary,
            "output": run.output,
            "error": run.error,
            "review_outcome": (
                run.review_outcome.value
                if hasattr(run.review_outcome, "value")
                else run.review_outcome
            ),
            "review_notes": run.review_notes,
            "duration_ms": run.duration_ms,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }

    def _thread_for(
        self, employee: AIEmployee, work_item: WorkItem | None, provider_id
    ) -> ConversationThread:
        stmt = select(ConversationThread).where(ConversationThread.ai_employee_id == employee.id)
        if work_item is not None:
            stmt = stmt.where(ConversationThread.work_item_id == work_item.id)
        thread = self.db.scalar(stmt)
        if thread is None:
            thread = ConversationThread(
                ai_employee_id=employee.id,
                work_item_id=work_item.id if work_item else None,
                provider_id=provider_id,
                title=f"{employee.name} — {work_item.task_code if work_item else 'general'}",
                status="active",
            )
            self.db.add(thread)
            self.db.flush()
        return thread

    def _next_seq(self, thread_id: uuid.UUID) -> int:
        rows = self.db.scalars(
            select(ExecutionMessage.sequence).where(ExecutionMessage.thread_id == thread_id)
        ).all()
        return (max(rows) + 1) if rows else 0

    def run_stage(
        self,
        employee_id: uuid.UUID,
        work_item_id: uuid.UUID | None = None,
        provider_name: str | None = None,
    ) -> dict:
        employee = self.db.get(AIEmployee, employee_id)
        if employee is None:
            raise NotFoundError(f"AI employee {employee_id} not found")
        work_item = self.db.get(WorkItem, work_item_id) if work_item_id else None

        if provider_name:
            provider_row = self.providers.get_by_name(provider_name)
            if provider_row is None:
                raise ValidationError(f"Unknown provider '{provider_name}'")
        else:
            provider_row = self.providers.provider_for_employee(employee)

        thread = self._thread_for(employee, work_item, provider_row.id)
        context = self.context_builder.build(employee, work_item)
        prior = [
            Message(role=m.role.value if hasattr(m.role, "value") else m.role, content=m.content)
            for m in self.memory.short_term(thread.id)
        ]
        messages, version = self.prompt_builder.build(context, prior)

        run = ExecutionRun(
            thread_id=thread.id,
            ai_employee_id=employee.id,
            work_item_id=work_item.id if work_item else None,
            provider_id=provider_row.id,
            prompt_version=version,
            model=provider_row.default_model,
            status=RunStatus.RUNNING,
            input_summary=(context.get("task") or {}).get("title") or "General duties",
            started_at=_now(),
        )
        self.db.add(run)
        self.db.flush()

        seq = self._next_seq(thread.id)
        for m in messages:
            self.db.add(
                ExecutionMessage(
                    thread_id=thread.id, run_id=run.id, role=m.role, content=m.content, sequence=seq
                )
            )
            seq += 1

        request = ExecutionRequest(
            messages=messages,
            model=provider_row.default_model,
            metadata={
                "role": context["employee"]["role"],
                "task": (context.get("task") or {}).get("title", "the assigned task"),
            },
        )

        result = None
        last_error = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                provider = self.providers.instance_for(provider_row)
                result = provider.execute(request)
                self.db.add(RetryHistory(run_id=run.id, attempt=attempt, status="succeeded"))
                break
            except ProviderError as exc:
                last_error = str(exc)
                self.db.add(
                    RetryHistory(run_id=run.id, attempt=attempt, status="failed", error=last_error)
                )

        # Provider health record.
        try:
            h = self.providers.instance_for(provider_row).health()
            self.db.add(
                ProviderHealthRecord(provider_id=provider_row.id, status=h.status, detail=h.detail)
            )
        except Exception:  # pragma: no cover
            pass

        if result is None:
            run.status = RunStatus.FAILED
            run.error = last_error
            run.completed_at = _now()
            self.db.flush()
            return self.serialize_run(run)

        # Success — persist output, message, metrics, usage, cost.
        run.status = RunStatus.COMPLETED
        run.output = result.output
        run.completed_at = _now()
        run.duration_ms = result.latency_ms
        self.db.add(
            ExecutionMessage(
                thread_id=thread.id,
                run_id=run.id,
                role=MessageRole.ASSISTANT,
                content=result.output,
                sequence=seq,
            )
        )
        self.db.add(
            ExecutionMetric(
                run_id=run.id,
                latency_ms=result.latency_ms,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens,
            )
        )
        self.db.add(
            TokenUsage(
                run_id=run.id,
                provider_id=provider_row.id,
                ai_employee_id=employee.id,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens,
            )
        )
        self.db.add(
            CostTracking(
                run_id=run.id,
                provider_id=provider_row.id,
                tokens=result.total_tokens,
                estimated_cost=result.cost,
                currency=result.currency,
            )
        )
        self.db.flush()
        return self.serialize_run(run)

    def run_workflow(self, work_item_id: uuid.UUID, provider_name: str | None = None) -> list[dict]:
        """Run a stage for each handoff recipient in sequence (persists each)."""
        handoffs = list(
            self.db.scalars(
                select(Handoff)
                .where(Handoff.work_item_id == work_item_id)
                .order_by(Handoff.sequence)
            ).all()
        )
        runs = []
        for h in handoffs:
            runs.append(self.run_stage(h.to_ai_employee_id, work_item_id, provider_name))
        return runs

    def review_run(
        self, run_id: uuid.UUID, outcome: ReviewOutcome, notes: str | None = None
    ) -> dict:
        run = self.db.get(ExecutionRun, run_id)
        if run is None:
            raise NotFoundError(f"Run {run_id} not found")
        run.review_outcome = outcome
        run.review_notes = notes
        self.db.flush()
        return self.serialize_run(run)

    # -- reads / dashboards -----------------------------------------------

    def list_runs(self, *, status: str | None = None, limit: int = 50) -> list[dict]:
        stmt = select(ExecutionRun).order_by(ExecutionRun.created_at.desc()).limit(limit)
        if status:
            stmt = (
                select(ExecutionRun)
                .where(ExecutionRun.status == status)
                .order_by(ExecutionRun.created_at.desc())
                .limit(limit)
            )
        return [self.serialize_run(r) for r in self.db.scalars(stmt).all()]

    def get_run(self, run_id: uuid.UUID) -> dict:
        run = self.db.get(ExecutionRun, run_id)
        if run is None:
            raise NotFoundError(f"Run {run_id} not found")
        return self.serialize_run(run)

    def thread_messages(self, thread_id: uuid.UUID) -> list[dict]:
        msgs = self.memory.conversation(thread_id)
        return [
            {
                "id": str(m.id),
                "role": m.role.value if hasattr(m.role, "value") else m.role,
                "content": m.content,
                "sequence": m.sequence,
            }
            for m in msgs
        ]

    def founder_dashboard(self) -> dict:
        runs = list(self.db.scalars(select(ExecutionRun)).all())
        usage = list(self.db.scalars(select(TokenUsage)).all())
        costs = list(self.db.scalars(select(CostTracking)).all())
        durations = [r.duration_ms for r in runs if r.duration_ms is not None]
        providers = [self.providers.serialize(p) for p in self.providers.list_providers()]
        return {
            "providers": [
                {
                    "name": p["name"],
                    "enabled": p["enabled"],
                    "is_default": p["is_default"],
                    "health": p["health"],
                }
                for p in providers
            ],
            "running_executions": sum(
                1
                for r in runs
                if (r.status.value if hasattr(r.status, "value") else r.status) == "running"
            ),
            "failed_executions": sum(
                1
                for r in runs
                if (r.status.value if hasattr(r.status, "value") else r.status) == "failed"
            ),
            "completed_executions": sum(
                1
                for r in runs
                if (r.status.value if hasattr(r.status, "value") else r.status) == "completed"
            ),
            "execution_queue": len(runs),
            "token_usage": sum(u.total_tokens for u in usage),
            "estimated_cost": round(sum(c.estimated_cost for c in costs), 6),
            "avg_runtime_ms": round(sum(durations) / len(durations)) if durations else None,
        }

    def ai_dashboard(self, employee_id: uuid.UUID) -> dict:
        employee = self.db.get(AIEmployee, employee_id)
        if employee is None:
            raise NotFoundError(f"AI employee {employee_id} not found")
        thread = self.db.scalar(
            select(ConversationThread)
            .where(ConversationThread.ai_employee_id == employee_id)
            .order_by(ConversationThread.updated_at.desc())
        )
        runs = list(
            self.db.scalars(
                select(ExecutionRun)
                .where(ExecutionRun.ai_employee_id == employee_id)
                .order_by(ExecutionRun.created_at.desc())
            ).all()
        )
        provider = self.providers.provider_for_employee(employee)
        last = runs[0] if runs else None
        return {
            "employee": {"id": str(employee.id), "name": employee.name},
            "current_provider": provider.name,
            "current_thread": str(thread.id) if thread else None,
            "current_context": {
                "role": employee.role.title if employee.role else None,
                "department": employee.department.name if employee.department else None,
            },
            "last_prompt": last.input_summary if last else None,
            "last_response": last.output if last else None,
            "memory_messages": len(self.memory.conversation(thread.id)) if thread else 0,
            "execution_history": len(runs),
        }
