"""Autonomous Development Engine endpoints (Sprint 13).

Create + run development tasks (plan → generate → modify → test → review →
document → git → PR), inspect the full implementation, and approve/reject the
pull request. Reads: dev:read (all roles); run: dev:execute (Founder + Director);
approve: dev:approve (Founder only). No auto-merge, no auto-push.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import (
    get_approval_dev_service,
    get_db,
    get_development_service,
    require_permission,
)
from app.domain.development_enums import ApprovalDecision
from app.domain.roles import Permission

router = APIRouter(prefix="/development", tags=["development"])
_read = Depends(require_permission(Permission.DEV_READ))
_execute = Depends(require_permission(Permission.DEV_EXECUTE))
_approve = Depends(require_permission(Permission.DEV_APPROVE))


class ModificationSpecIn(BaseModel):
    """Existing-code modification intent. When present, the workflow modifies an
    existing file (or creates/deletes/renames) instead of scaffolding a new module.
    The workflow auto-selects CREATE / MODIFY / DELETE / RENAME from the target."""

    target_file: str = Field(min_length=1, max_length=1000)
    operation: str = Field(
        default="insert_after_anchor",
        description="insert_after_anchor | insert_before_anchor | add_function | "
        "add_method | replace_function | remove_symbol | rename_symbol | "
        "delete_file | rename_file",
    )
    source_root: str | None = None
    anchor: str | None = None
    snippet: str | None = None
    occurrence: int | None = None
    name: str | None = None
    class_name: str | None = None
    old_name: str | None = None
    new_name: str | None = None
    new_path: str | None = None
    content: str | None = None
    imports: list[str] | None = None


class CreateTaskIn(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str | None = None
    work_item_id: uuid.UUID | None = None
    repository_id: uuid.UUID | None = None
    ai_employee_id: uuid.UUID | None = None
    provider_name: str | None = None
    modification: ModificationSpecIn | None = None


class RunIn(BaseModel):
    provider_name: str | None = None


class ApprovalIn(BaseModel):
    decision: ApprovalDecision
    notes: str | None = None
    override: bool = False  # Founder override of a failing quality gate


@router.get("/tasks", dependencies=[_read])
def list_tasks(
    status_filter: str | None = Query(default=None, alias="status"),
    service=Depends(get_development_service),
) -> dict:
    items = service.list_tasks(status=status_filter)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/tasks", dependencies=[_execute])
def create_task(payload: CreateTaskIn, service=Depends(get_development_service)) -> dict:
    task = service.create_task(
        payload.title,
        description=payload.description,
        work_item_id=payload.work_item_id,
        repository_id=payload.repository_id,
        ai_employee_id=payload.ai_employee_id,
        modification_spec=(
            payload.modification.model_dump(exclude_none=True) if payload.modification else None
        ),
    )
    return {"data": service.serialize(task)}


@router.get("/tasks/{task_id}", dependencies=[_read])
def get_task(task_id: uuid.UUID, service=Depends(get_development_service)) -> dict:
    return {"data": service.get_task(task_id)}


@router.post("/tasks/{task_id}/run", dependencies=[_execute])
def run_task(task_id: uuid.UUID, payload: RunIn, service=Depends(get_development_service)) -> dict:
    return {"data": service.run_workflow(task_id, payload.provider_name)}


@router.post("/tasks/{task_id}/run-async", dependencies=[_execute])
def run_task_async(task_id: uuid.UUID, payload: RunIn, db=Depends(get_db)) -> dict:
    """Durable background execution (WP3): enqueue the workflow as a job that
    survives restarts. The synchronous /run endpoint is unchanged."""
    from app.services.job_queue import JobQueue

    job = JobQueue(db).enqueue(
        "development_workflow",
        {"task_id": str(task_id), "provider_name": payload.provider_name},
        idempotency_key=f"dev-workflow:{task_id}",
    )
    return {"data": JobQueue(db).serialize(job)}


@router.post("/run", dependencies=[_execute])
def create_and_run(payload: CreateTaskIn, service=Depends(get_development_service)) -> dict:
    """Convenience: create a task and immediately run the full workflow."""
    task = service.create_task(
        payload.title,
        description=payload.description,
        work_item_id=payload.work_item_id,
        repository_id=payload.repository_id,
        ai_employee_id=payload.ai_employee_id,
        modification_spec=(
            payload.modification.model_dump(exclude_none=True) if payload.modification else None
        ),
    )
    return {"data": service.run_workflow(task.id, payload.provider_name)}


@router.get("/tasks/{task_id}/timeline", dependencies=[_read])
def timeline(task_id: uuid.UUID, service=Depends(get_development_service)) -> dict:
    items = service.timeline(task_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/team", dependencies=[_read])
def ai_team(service=Depends(get_development_service)) -> dict:
    """The acting AI engineering team (WP7): real employees, responsibilities,
    decision rules, authority, and selected provider."""
    items = service.team()
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/tasks/{task_id}/orchestration", dependencies=[_read])
def orchestration(task_id: uuid.UUID, service=Depends(get_development_service)) -> dict:
    """Which employee performed each stage + the handoffs between them."""
    return {"data": service.orchestration(task_id)}


@router.post("/tasks/{task_id}/approve", dependencies=[_approve])
def approve(
    task_id: uuid.UUID,
    payload: ApprovalIn,
    approval=Depends(get_approval_dev_service),
    service=Depends(get_development_service),
) -> dict:
    approval.decide(task_id, payload.decision, payload.notes, override=payload.override)
    from app.services.audit import AuditService

    dec = payload.decision.value if hasattr(payload.decision, "value") else payload.decision
    AuditService(service.db).record(
        "pr_approval",
        category="approval",
        entity_type="dev_task",
        entity_id=str(task_id),
        detail=f"decision={dec} override={payload.override}",
    )
    return {"data": service.get_task(task_id)}


@router.get("/pending-approvals", dependencies=[_read])
def pending_approvals(
    approval=Depends(get_approval_dev_service), service=Depends(get_development_service)
) -> dict:
    items = [service.serialize(t) for t in approval.pending()]
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/founder-dashboard", dependencies=[_read])
def founder_dashboard(service=Depends(get_development_service)) -> dict:
    return {"data": service.founder_dashboard()}


@router.get("/ai-dashboard", dependencies=[_read])
def ai_dashboard(
    task_id: uuid.UUID | None = Query(default=None),
    service=Depends(get_development_service),
) -> dict:
    return {"data": service.ai_dashboard(task_id)}
