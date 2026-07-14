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
    get_development_service,
    require_permission,
)
from app.domain.development_enums import ApprovalDecision
from app.domain.roles import Permission

router = APIRouter(prefix="/development", tags=["development"])
_read = Depends(require_permission(Permission.DEV_READ))
_execute = Depends(require_permission(Permission.DEV_EXECUTE))
_approve = Depends(require_permission(Permission.DEV_APPROVE))


class CreateTaskIn(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str | None = None
    work_item_id: uuid.UUID | None = None
    repository_id: uuid.UUID | None = None
    ai_employee_id: uuid.UUID | None = None
    provider_name: str | None = None


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
    )
    return {"data": service.serialize(task)}


@router.get("/tasks/{task_id}", dependencies=[_read])
def get_task(task_id: uuid.UUID, service=Depends(get_development_service)) -> dict:
    return {"data": service.get_task(task_id)}


@router.post("/tasks/{task_id}/run", dependencies=[_execute])
def run_task(task_id: uuid.UUID, payload: RunIn, service=Depends(get_development_service)) -> dict:
    return {"data": service.run_workflow(task_id, payload.provider_name)}


@router.post("/run", dependencies=[_execute])
def create_and_run(payload: CreateTaskIn, service=Depends(get_development_service)) -> dict:
    """Convenience: create a task and immediately run the full workflow."""
    task = service.create_task(
        payload.title,
        description=payload.description,
        work_item_id=payload.work_item_id,
        repository_id=payload.repository_id,
        ai_employee_id=payload.ai_employee_id,
    )
    return {"data": service.run_workflow(task.id, payload.provider_name)}


@router.get("/tasks/{task_id}/timeline", dependencies=[_read])
def timeline(task_id: uuid.UUID, service=Depends(get_development_service)) -> dict:
    items = service.timeline(task_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/tasks/{task_id}/approve", dependencies=[_approve])
def approve(
    task_id: uuid.UUID,
    payload: ApprovalIn,
    approval=Depends(get_approval_dev_service),
    service=Depends(get_development_service),
) -> dict:
    approval.decide(task_id, payload.decision, payload.notes, override=payload.override)
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
