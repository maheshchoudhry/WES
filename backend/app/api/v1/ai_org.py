"""AI organization workspace endpoints: org chart, department view, summary."""

from fastapi import APIRouter, Depends

from app.api.deps import get_ai_reporting_service, require_permission
from app.domain.roles import Permission
from app.services.ai_reporting import AIReportingService

router = APIRouter(prefix="/ai-org", tags=["ai-organization"])

_read = Depends(require_permission(Permission.AI_READ))


@router.get("/chart", dependencies=[_read])
def org_chart(service: AIReportingService = Depends(get_ai_reporting_service)) -> dict:
    return {"data": service.org_chart()}


@router.get("/departments", dependencies=[_read])
def department_view(service: AIReportingService = Depends(get_ai_reporting_service)) -> dict:
    items = service.department_view()
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/summary", dependencies=[_read])
def organization_summary(
    service: AIReportingService = Depends(get_ai_reporting_service),
) -> dict:
    return {"data": service.summary()}
