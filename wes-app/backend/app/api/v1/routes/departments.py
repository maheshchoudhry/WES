"""Department CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Pagination
from app.db.session import get_db
from app.schemas.common import Page, PageMeta
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services.department import DepartmentService

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=Page[DepartmentRead])
def list_departments(page: Pagination = Depends(), db: Session = Depends(get_db)) -> Page:
    items, total = DepartmentService(db).list(page.offset, page.limit)
    return Page[DepartmentRead](
        data=[DepartmentRead.model_validate(i) for i in items],
        pagination=PageMeta(page=page.page, page_size=page.page_size, total=total),
    )


@router.post("", response_model=DepartmentRead, status_code=201)
def create_department(
    payload: DepartmentCreate, db: Session = Depends(get_db)
) -> DepartmentRead:
    return DepartmentService(db).create(payload)


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department(department_id: int, db: Session = Depends(get_db)) -> DepartmentRead:
    return DepartmentService(db).get(department_id)


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: int, payload: DepartmentUpdate, db: Session = Depends(get_db)
) -> DepartmentRead:
    return DepartmentService(db).update(department_id, payload)


@router.delete("/{department_id}", status_code=204)
def delete_department(department_id: int, db: Session = Depends(get_db)) -> None:
    DepartmentService(db).delete(department_id)
