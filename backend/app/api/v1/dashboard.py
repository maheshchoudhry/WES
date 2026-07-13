"""Executive Dashboard read-only aggregation endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.domain.roles import Permission
from app.services.dashboard import DashboardService

# Every dashboard endpoint is read-only and requires the dashboard:read permission
# (granted to all authenticated roles).
router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_permission(Permission.DASHBOARD_READ))],
)


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


@router.get("/company-summary")
def company_summary(service: DashboardService = Depends(get_dashboard_service)) -> dict:
    return {"data": service.company_summary()}


@router.get("/stats")
def dashboard_stats(service: DashboardService = Depends(get_dashboard_service)) -> dict:
    return {"data": service.stats()}


@router.get("/departments")
def department_stats(service: DashboardService = Depends(get_dashboard_service)) -> dict:
    items = service.department_stats()
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/employees")
def employee_directory(service: DashboardService = Depends(get_dashboard_service)) -> dict:
    items = service.employee_directory()
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/activity")
def recent_activity(
    limit: int = Query(10, ge=1, le=50),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    items = service.recent_activity(limit=limit)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/health")
def system_health(service: DashboardService = Depends(get_dashboard_service)) -> dict:
    return {"data": service.system_health()}
