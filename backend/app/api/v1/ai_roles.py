"""AI Role and AI Department listing endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_ai_org_service, require_permission
from app.domain.roles import Permission
from app.schemas.ai import AIDepartmentRead, AIRoleRead
from app.services.ai_organization import AIOrganizationService

router = APIRouter(tags=["ai-organization"])

_read = Depends(require_permission(Permission.AI_READ))


@router.get("/ai-roles", dependencies=[_read])
def list_ai_roles(service: AIOrganizationService = Depends(get_ai_org_service)) -> dict:
    roles = service.roles.list_all()
    return {"data": [AIRoleRead.model_validate(r) for r in roles], "meta": {"total": len(roles)}}


@router.get("/ai-departments", dependencies=[_read])
def list_ai_departments(service: AIOrganizationService = Depends(get_ai_org_service)) -> dict:
    depts = service.departments.list_all()
    return {
        "data": [AIDepartmentRead.model_validate(d) for d in depts],
        "meta": {"total": len(depts)},
    }
