"""AI Provider platform endpoints (Settings, connection testing, models, budget,
cost, metrics, and events). Reads: ORCH_READ; writes: ORCH_WRITE (Founder)."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import (
    get_budget_service,
    get_cost_engine,
    get_health_monitor,
    get_metrics_service,
    get_platform_dashboard,
    get_provider_service,
    require_permission,
)
from app.domain.roles import Permission
from app.services.providers_service import ProviderService

router = APIRouter(prefix="/providers", tags=["providers"])
_read = Depends(require_permission(Permission.ORCH_READ))
_write = Depends(require_permission(Permission.ORCH_WRITE))


class EnabledIn(BaseModel):
    enabled: bool


class ConfigIn(BaseModel):
    key: str
    value: str | None = None


class RoleMapIn(BaseModel):
    role_code: str
    provider_name: str


class SecretIn(BaseModel):
    value: str = Field(min_length=8)
    key_name: str = "api_key"


class ModelIn(BaseModel):
    code: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    is_default: bool = False
    context_window: int | None = None
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0


class ActiveModelIn(BaseModel):
    model_code: str


class PriorityIn(BaseModel):
    priority: int


class BudgetIn(BaseModel):
    daily_cost_limit: float | None = None
    monthly_cost_limit: float | None = None
    max_cost: float | None = None
    max_tokens: int | None = None
    warning_threshold: float | None = None
    hard_stop: bool | None = None


@router.get("", dependencies=[_read])
def list_providers(service: ProviderService = Depends(get_provider_service)) -> dict:
    items = [service.serialize(p) for p in service.list_providers()]
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/role-mappings", dependencies=[_read])
def role_mappings(service: ProviderService = Depends(get_provider_service)) -> dict:
    return {"data": service.role_mappings()}


@router.post("/health-check", dependencies=[_read])
def health_check(service: ProviderService = Depends(get_provider_service)) -> dict:
    return {"data": service.check_health()}


@router.patch("/{provider_id}/enabled", dependencies=[_write])
def set_enabled(
    provider_id: uuid.UUID,
    payload: EnabledIn,
    service: ProviderService = Depends(get_provider_service),
) -> dict:
    service.set_enabled(provider_id, payload.enabled)
    return {"data": service.serialize(service.get(provider_id))}


@router.post("/{provider_id}/default", dependencies=[_write])
def set_default(
    provider_id: uuid.UUID, service: ProviderService = Depends(get_provider_service)
) -> dict:
    service.set_default(provider_id)
    return {"data": service.serialize(service.get(provider_id))}


@router.post("/{provider_id}/config", dependencies=[_write])
def set_config(
    provider_id: uuid.UUID,
    payload: ConfigIn,
    service: ProviderService = Depends(get_provider_service),
) -> dict:
    service.set_config(provider_id, payload.key, payload.value)
    return {"data": service.serialize(service.get(provider_id))}


@router.post("/role-mappings", dependencies=[_write])
def map_role(payload: RoleMapIn, service: ProviderService = Depends(get_provider_service)) -> dict:
    service.map_role(payload.role_code, payload.provider_name)
    return {"data": service.role_mappings()}


# --- Live provider platform (Sprint 11) -----------------------------------


@router.get("/dashboard", dependencies=[_read])
def platform_dashboard(dash=Depends(get_platform_dashboard)) -> dict:
    return {"data": dash.founder()}


@router.get("/ai-dashboard/{employee_id}", dependencies=[_read])
def platform_ai_dashboard(employee_id: uuid.UUID, dash=Depends(get_platform_dashboard)) -> dict:
    return {"data": dash.ai(employee_id)}


@router.get("/metrics", dependencies=[_read])
def provider_metrics(metrics=Depends(get_metrics_service)) -> dict:
    return {"data": metrics.provider_metrics()}


@router.get("/events", dependencies=[_read])
def provider_events(metrics=Depends(get_metrics_service)) -> dict:
    items = metrics.recent_events(50)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/cost", dependencies=[_read])
def provider_cost(group_by: str = "provider", cost=Depends(get_cost_engine)) -> dict:
    items = cost.aggregate(group_by)
    return {"data": items, "meta": {"group_by": group_by, "total": len(items)}}


@router.get("/budget", dependencies=[_read])
def get_budget(budget=Depends(get_budget_service)) -> dict:
    return {"data": budget.status()}


@router.put("/budget", dependencies=[_write])
def update_budget(payload: BudgetIn, budget=Depends(get_budget_service)) -> dict:
    budget.update_config(**payload.model_dump(exclude_none=True))
    return {"data": budget.status()}


@router.post("/monitor", dependencies=[_read])
def monitor(monitor_svc=Depends(get_health_monitor)) -> dict:
    return {"data": monitor_svc.monitor_all()}


@router.post("/{provider_id}/test", dependencies=[_read])
def test_connection(
    provider_id: uuid.UUID, service: ProviderService = Depends(get_provider_service)
) -> dict:
    return {"data": service.test_connection(provider_id)}


@router.post("/{provider_id}/secret", dependencies=[_write])
def set_secret(
    provider_id: uuid.UUID,
    payload: SecretIn,
    service: ProviderService = Depends(get_provider_service),
) -> dict:
    service.set_secret(provider_id, payload.value, payload.key_name)
    return {"data": service.serialize(service.get(provider_id))}


@router.get("/{provider_id}/models", dependencies=[_read])
def list_models(
    provider_id: uuid.UUID, service: ProviderService = Depends(get_provider_service)
) -> dict:
    items = [service.serialize_model(m) for m in service.models_for(provider_id)]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/{provider_id}/models", dependencies=[_write])
def add_model(
    provider_id: uuid.UUID,
    payload: ModelIn,
    service: ProviderService = Depends(get_provider_service),
) -> dict:
    m = service.add_model(
        provider_id,
        payload.code,
        payload.display_name,
        is_default=payload.is_default,
        context_window=payload.context_window,
        input_cost_per_1k=payload.input_cost_per_1k,
        output_cost_per_1k=payload.output_cost_per_1k,
    )
    return {"data": service.serialize_model(m)}


@router.post("/{provider_id}/active-model", dependencies=[_write])
def set_active_model(
    provider_id: uuid.UUID,
    payload: ActiveModelIn,
    service: ProviderService = Depends(get_provider_service),
) -> dict:
    service.set_active_model(provider_id, payload.model_code)
    return {"data": service.serialize(service.get(provider_id))}


@router.post("/{provider_id}/priority", dependencies=[_write])
def set_priority(
    provider_id: uuid.UUID,
    payload: PriorityIn,
    service: ProviderService = Depends(get_provider_service),
) -> dict:
    service.set_priority(provider_id, payload.priority)
    return {"data": service.serialize(service.get(provider_id))}
