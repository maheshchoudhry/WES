"""Prompt Library, SOP Library, and Decision Rules endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_execution_service, require_permission
from app.domain.roles import Permission
from app.schemas.execution import PromptCreate, SOPCreate
from app.services.execution import ExecutionService

router = APIRouter(tags=["libraries"])
_read = Depends(require_permission(Permission.EXEC_READ))
_write = Depends(require_permission(Permission.EXEC_WRITE))


@router.get("/prompts", dependencies=[_read])
def list_prompts(service: ExecutionService = Depends(get_execution_service)) -> dict:
    items = service.list_prompts()
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/prompts/{prompt_id}", dependencies=[_read])
def get_prompt(
    prompt_id: uuid.UUID, service: ExecutionService = Depends(get_execution_service)
) -> dict:
    return {"data": service.get_prompt(prompt_id)}


@router.post("/prompts", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_prompt(
    payload: PromptCreate, service: ExecutionService = Depends(get_execution_service)
) -> dict:
    return {"data": service.create_prompt(payload)}


@router.get("/sops", dependencies=[_read])
def list_sops(service: ExecutionService = Depends(get_execution_service)) -> dict:
    items = service.list_sops()
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/sops/{sop_id}", dependencies=[_read])
def get_sop(sop_id: uuid.UUID, service: ExecutionService = Depends(get_execution_service)) -> dict:
    return {"data": service.get_sop(sop_id)}


@router.post("/sops", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_sop(
    payload: SOPCreate, service: ExecutionService = Depends(get_execution_service)
) -> dict:
    return {"data": service.create_sop(payload)}


@router.get("/decision-rules", dependencies=[_read])
def list_decision_rules(
    role_id: uuid.UUID | None = Query(default=None),
    service: ExecutionService = Depends(get_execution_service),
) -> dict:
    items = service.list_decision_rules(role_id)
    return {"data": items, "meta": {"total": len(items)}}
