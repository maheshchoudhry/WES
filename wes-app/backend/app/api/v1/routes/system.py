"""System metadata endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.repositories.company import CompanyRepository
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/metadata")
def system_metadata(db: Session = Depends(get_db)) -> dict:
    return {
        "data": {
            "appName": settings.app_name,
            "apiVersion": settings.api_version,
            "schemaVersion": "0001",
            "counts": {
                "companies": CompanyRepository(db).count(),
                "departments": DepartmentRepository(db).count(),
                "employees": EmployeeRepository(db).count(),
            },
        }
    }
