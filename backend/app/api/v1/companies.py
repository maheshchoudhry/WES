"""Company REST CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import Pagination, get_company_service, pagination, require_permission
from app.domain.roles import Permission
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.services.company import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])

_read = Depends(require_permission(Permission.COMPANY_READ))
_write = Depends(require_permission(Permission.COMPANY_WRITE))


@router.get("", dependencies=[_read])
def list_companies(
    page: Pagination = Depends(pagination),
    service: CompanyService = Depends(get_company_service),
) -> dict:
    items, total = service.list(offset=page.offset, limit=page.limit)
    return {
        "data": [CompanyRead.model_validate(i) for i in items],
        "meta": {"total": total},
    }


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_company(
    payload: CompanyCreate,
    service: CompanyService = Depends(get_company_service),
) -> dict:
    company = service.create(payload)
    return {"data": CompanyRead.model_validate(company)}


@router.get("/{company_id}", dependencies=[_read])
def get_company(
    company_id: uuid.UUID,
    service: CompanyService = Depends(get_company_service),
) -> dict:
    return {"data": CompanyRead.model_validate(service.get(company_id))}


@router.patch("/{company_id}", dependencies=[_write])
def update_company(
    company_id: uuid.UUID,
    payload: CompanyUpdate,
    service: CompanyService = Depends(get_company_service),
) -> dict:
    company = service.update(company_id, payload)
    return {"data": CompanyRead.model_validate(company)}


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_write])
def delete_company(
    company_id: uuid.UUID,
    service: CompanyService = Depends(get_company_service),
) -> None:
    service.delete(company_id)
