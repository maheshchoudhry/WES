"""Enterprise DevOps Platform endpoints (Sprint 15).

CI/CD pipelines, deployments, releases, environments, monitoring, incidents, and
rollback. Reads: devops:read (all). Run pipeline / deploy staging: devops:execute
(Founder + Director). Production deploy + rollback: devops:production (Founder)."""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import (
    get_current_user,
    get_deployment_service,
    get_environment_service,
    get_health_service,
    get_incident_service,
    get_monitoring_service,
    get_pipeline_service,
    get_release_service,
    get_rollback_service,
    require_permission,
)
from app.domain.roles import Permission

router = APIRouter(prefix="/devops", tags=["devops"])
_read = Depends(require_permission(Permission.DEVOPS_READ))
_execute = Depends(require_permission(Permission.DEVOPS_EXECUTE))
_production = Depends(require_permission(Permission.DEVOPS_PRODUCTION))


class RunPipelineIn(BaseModel):
    task_id: uuid.UUID
    environment: str = "staging"


class RollbackIn(BaseModel):
    environment: str
    to_release_id: uuid.UUID
    reason: str | None = None


# --- pipelines ------------------------------------------------------------


@router.get("/pipelines", dependencies=[_read])
def list_pipelines(
    status_filter: str | None = Query(default=None, alias="status"),
    service=Depends(get_pipeline_service),
) -> dict:
    items = service.list_pipelines(status=status_filter)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/pipelines/run", dependencies=[_execute])
def run_pipeline(payload: RunPipelineIn, service=Depends(get_pipeline_service)) -> dict:
    pipe = service.run(payload.task_id, payload.environment)
    return {"data": service.serialize(pipe, full=True)}


@router.get("/pipelines/{pipeline_id}", dependencies=[_read])
def get_pipeline(pipeline_id: uuid.UUID, service=Depends(get_pipeline_service)) -> dict:
    return {"data": service.get_pipeline(pipeline_id)}


@router.post("/pipelines/{pipeline_id}/deploy-production", dependencies=[_production])
def deploy_production(
    pipeline_id: uuid.UUID,
    user=Depends(get_current_user),
    service=Depends(get_pipeline_service),
) -> dict:
    return {"data": service.deploy_production(pipeline_id, user.full_name)}


# --- deployments / releases / environments --------------------------------


@router.get("/deployments", dependencies=[_read])
def list_deployments(
    environment: str | None = Query(default=None), service=Depends(get_deployment_service)
) -> dict:
    items = service.list_deployments(environment=environment)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/releases", dependencies=[_read])
def list_releases(service=Depends(get_release_service)) -> dict:
    items = service.history()
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/environments", dependencies=[_read])
def list_environments(service=Depends(get_environment_service)) -> dict:
    items = [service.serialize(e) for e in service.list_environments()]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/rollback", dependencies=[_production])
def rollback(payload: RollbackIn, service=Depends(get_rollback_service)) -> dict:
    history = service.rollback(payload.environment, payload.to_release_id, payload.reason)
    return {
        "data": {
            "status": history.status.value if hasattr(history.status, "value") else history.status
        }
    }


@router.get("/rollback-history", dependencies=[_read])
def rollback_history(service=Depends(get_rollback_service)) -> dict:
    items = service.history()
    return {"data": items, "meta": {"total": len(items)}}


# --- monitoring / incidents -----------------------------------------------


@router.post("/monitoring/snapshot", dependencies=[_read])
def monitoring_snapshot(service=Depends(get_health_service)) -> dict:
    return {"data": service.serialize(service.snapshot())}


@router.get("/monitoring/health", dependencies=[_read])
def monitoring_health(service=Depends(get_health_service)) -> dict:
    latest = service.latest()
    return {"data": service.serialize(latest) if latest else None}


@router.get("/monitoring/events", dependencies=[_read])
def monitoring_events(service=Depends(get_monitoring_service)) -> dict:
    items = service.recent_events()
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/incidents", dependencies=[_read])
def list_incidents(
    status_filter: str | None = Query(default=None, alias="status"),
    service=Depends(get_incident_service),
) -> dict:
    items = service.list_incidents(status=status_filter)
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/incidents/{incident_id}/resolve", dependencies=[_execute])
def resolve_incident(incident_id: uuid.UUID, service=Depends(get_incident_service)) -> dict:
    return {"data": service.serialize(service.resolve(incident_id))}


# --- dashboards -----------------------------------------------------------


@router.get("/founder-dashboard", dependencies=[_read])
def founder_dashboard(service=Depends(get_pipeline_service)) -> dict:
    return {"data": service.founder_dashboard()}


@router.get("/ai-dashboard", dependencies=[_read])
def ai_dashboard(
    pipeline_id: uuid.UUID | None = Query(default=None), service=Depends(get_pipeline_service)
) -> dict:
    return {"data": service.ai_dashboard(pipeline_id)}
