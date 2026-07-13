"""Kanban board and work analytics for dashboards."""

import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_work_analytics_service,
    get_work_service,
    require_permission,
)
from app.domain.roles import Permission
from app.services.work import WorkService
from app.services.work_analytics import WorkAnalyticsService

router = APIRouter(prefix="/work", tags=["work"])
_read = Depends(require_permission(Permission.WORK_READ))


@router.get("/kanban", dependencies=[_read])
def kanban(
    project_id: uuid.UUID | None = Query(default=None),
    service: WorkService = Depends(get_work_service),
) -> dict:
    return {"data": service.kanban(project_id=project_id)}


@router.get("/founder-summary", dependencies=[_read])
def founder_summary(
    service: WorkAnalyticsService = Depends(get_work_analytics_service),
) -> dict:
    return {"data": service.founder_summary()}


@router.get("/ai-summary", dependencies=[_read])
def ai_summary(service: WorkAnalyticsService = Depends(get_work_analytics_service)) -> dict:
    return {"data": service.ai_summary()}
