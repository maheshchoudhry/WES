"""AI Provider settings endpoints (Settings screen)."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_provider_service, require_permission
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
