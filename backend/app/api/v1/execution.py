"""AI Execution Engine endpoints: workspace, queue, history, reviews, handoffs."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_execution_service, require_permission
from app.domain.roles import Permission
from app.schemas.execution import (
    HandoffAdvance,
    QueueAdvance,
    QueueItemCreate,
    ReviewCreate,
    ReviewDecision,
)
from app.services.execution import ExecutionService

router = APIRouter(tags=["execution"])
_read = Depends(require_permission(Permission.EXEC_READ))
_write = Depends(require_permission(Permission.EXEC_WRITE))


# --- Workspace ---
@router.get("/workspaces/{employee_id}", dependencies=[_read])
def get_workspace(
    employee_id: uuid.UUID, service: ExecutionService = Depends(get_execution_service)
) -> dict:
    return {"data": service.get_workspace(employee_id)}


# --- Execution queue ---
@router.get("/execution-queue", dependencies=[_read])
def list_queue(
    ai_employee_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    service: ExecutionService = Depends(get_execution_service),
) -> dict:
    items = service.list_queue(ai_employee_id=ai_employee_id, status=status_filter)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/execution-queue", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_queue_item(
    payload: QueueItemCreate, service: ExecutionService = Depends(get_execution_service)
) -> dict:
    return {"data": service.create_queue_item(payload)}


@router.post("/execution-queue/{item_id}/advance", dependencies=[_write])
def advance_queue(
    item_id: uuid.UUID,
    payload: QueueAdvance,
    service: ExecutionService = Depends(get_execution_service),
) -> dict:
    return {"data": service.advance_queue(item_id, payload)}


# --- History ---
@router.get("/execution-history", dependencies=[_read])
def list_history(
    ai_employee_id: uuid.UUID | None = Query(default=None),
    service: ExecutionService = Depends(get_execution_service),
) -> dict:
    items = service.list_history(ai_employee_id=ai_employee_id)
    return {"data": items, "meta": {"total": len(items)}}


# --- Reviews ---
@router.get("/reviews", dependencies=[_read])
def list_reviews(
    reviewer_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    service: ExecutionService = Depends(get_execution_service),
) -> dict:
    items = service.list_reviews(reviewer_id=reviewer_id, status=status_filter)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/reviews", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_review(
    payload: ReviewCreate, service: ExecutionService = Depends(get_execution_service)
) -> dict:
    return {"data": service.create_review(payload)}


@router.post("/reviews/{review_id}/decision", dependencies=[_write])
def decide_review(
    review_id: uuid.UUID,
    payload: ReviewDecision,
    service: ExecutionService = Depends(get_execution_service),
) -> dict:
    return {"data": service.decide_review(review_id, payload)}


# --- Handoffs ---
@router.get("/handoffs", dependencies=[_read])
def list_handoffs(
    work_item_id: uuid.UUID | None = Query(default=None),
    service: ExecutionService = Depends(get_execution_service),
) -> dict:
    items = service.list_handoffs(work_item_id=work_item_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/handoffs/{handoff_id}/advance", dependencies=[_write])
def advance_handoff(
    handoff_id: uuid.UUID,
    payload: HandoffAdvance,
    service: ExecutionService = Depends(get_execution_service),
) -> dict:
    return {"data": service.advance_handoff(handoff_id, payload)}


# --- Dashboards ---
@router.get("/execution/founder-dashboard", dependencies=[_read])
def founder_dashboard(service: ExecutionService = Depends(get_execution_service)) -> dict:
    return {"data": service.founder_dashboard()}


@router.get("/execution/ai-dashboard", dependencies=[_read])
def ai_dashboard(service: ExecutionService = Depends(get_execution_service)) -> dict:
    return {"data": service.ai_dashboard()}
