"""Company CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Pagination
from app.db.session import get_db
from app.schemas.common import Page, PageMeta
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.services.company import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=Page[CompanyRead])
def list_companies(page: Pagination = Depends(), db: Session = Depends(get_db)) -> Page:
    items, total = CompanyService(db).list(page.offset, page.limit)
    return Page[CompanyRead](
        data=[CompanyRead.model_validate(i) for i in items],
        pagination=PageMeta(page=page.page, page_size=page.page_size, total=total),
    )


@router.post("", response_model=CompanyRead, status_code=201)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> CompanyRead:
    return CompanyService(db).create(payload)


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)) -> CompanyRead:
    return CompanyService(db).get(company_id)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)
) -> CompanyRead:
    return CompanyService(db).update(company_id, payload)


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int, db: Session = Depends(get_db)) -> None:
    CompanyService(db).delete(company_id)
