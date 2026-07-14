"""AI Orchestration endpoints: run pipeline, runs, threads, dashboards."""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_orchestration_service, require_permission
from app.domain.orchestration_enums import ReviewOutcome
from app.domain.roles import Permission
from app.services.orchestration import OrchestrationService

router = APIRouter(tags=["orchestration"])
_read = Depends(require_permission(Permission.ORCH_READ))
_write = Depends(require_permission(Permission.ORCH_WRITE))


class RunStageIn(BaseModel):
    ai_employee_id: uuid.UUID
    work_item_id: uuid.UUID | None = None
    provider_name: str | None = None


class RunWorkflowIn(BaseModel):
    work_item_id: uuid.UUID
    provider_name: str | None = None


class ReviewIn(BaseModel):
    outcome: ReviewOutcome
    notes: str | None = None


@router.post("/orchestration/run", dependencies=[_write])
def run_stage(
    payload: RunStageIn, service: OrchestrationService = Depends(get_orchestration_service)
) -> dict:
    return {
        "data": service.run_stage(
            payload.ai_employee_id, payload.work_item_id, payload.provider_name
        )
    }


@router.post("/orchestration/run-workflow", dependencies=[_write])
def run_workflow(
    payload: RunWorkflowIn, service: OrchestrationService = Depends(get_orchestration_service)
) -> dict:
    runs = service.run_workflow(payload.work_item_id, payload.provider_name)
    return {"data": runs, "meta": {"total": len(runs)}}


@router.get("/orchestration/runs", dependencies=[_read])
def list_runs(
    status_filter: str | None = Query(default=None, alias="status"),
    service: OrchestrationService = Depends(get_orchestration_service),
) -> dict:
    items = service.list_runs(status=status_filter)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/orchestration/runs/{run_id}", dependencies=[_read])
def get_run(
    run_id: uuid.UUID, service: OrchestrationService = Depends(get_orchestration_service)
) -> dict:
    return {"data": service.get_run(run_id)}


@router.post("/orchestration/runs/{run_id}/review", dependencies=[_write])
def review_run(
    run_id: uuid.UUID,
    payload: ReviewIn,
    service: OrchestrationService = Depends(get_orchestration_service),
) -> dict:
    return {"data": service.review_run(run_id, payload.outcome, payload.notes)}


@router.get("/orchestration/threads/{thread_id}/messages", dependencies=[_read])
def thread_messages(
    thread_id: uuid.UUID, service: OrchestrationService = Depends(get_orchestration_service)
) -> dict:
    items = service.thread_messages(thread_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/orchestration/founder-dashboard", dependencies=[_read])
def founder_dashboard(service: OrchestrationService = Depends(get_orchestration_service)) -> dict:
    return {"data": service.founder_dashboard()}


@router.get("/orchestration/ai-dashboard/{employee_id}", dependencies=[_read])
def ai_dashboard(
    employee_id: uuid.UUID, service: OrchestrationService = Depends(get_orchestration_service)
) -> dict:
    return {"data": service.ai_dashboard(employee_id)}
