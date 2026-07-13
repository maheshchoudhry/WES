"""Company service — business rules and orchestration for the Company domain."""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.company import Company
from app.repositories.company import CompanyRepository
from app.repositories.department import DepartmentRepository
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyService:
    def __init__(self, db: Session):
        self.db = db
        self.companies = CompanyRepository(db)
        self.departments = DepartmentRepository(db)

    def get(self, company_id: uuid.UUID) -> Company:
        company = self.companies.get(company_id)
        if company is None:
            raise NotFoundError(f"Company {company_id} not found")
        return company

    def list(self, *, offset: int = 0, limit: int = 100) -> tuple[list[Company], int]:
        return self.companies.list(offset=offset, limit=limit), self.companies.count()

    def create(self, payload: CompanyCreate) -> Company:
        if self.companies.get_by_slug(payload.slug):
            raise ConflictError(f"Company slug '{payload.slug}' already exists")
        if self.companies.get_by_name(payload.name):
            raise ConflictError(f"Company name '{payload.name}' already exists")
        company = Company(**payload.model_dump())
        return self.companies.add(company)

    def update(self, company_id: uuid.UUID, payload: CompanyUpdate) -> Company:
        company = self.get(company_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"] != company.name:
            existing = self.companies.get_by_name(data["name"])
            if existing and existing.id != company.id:
                raise ConflictError(f"Company name '{data['name']}' already exists")
        for field, value in data.items():
            setattr(company, field, value)
        self.db.flush()
        self.db.refresh(company)
        return company

    def delete(self, company_id: uuid.UUID) -> None:
        company = self.get(company_id)
        # Business rule: a company with departments cannot be deleted outright.
        if self.departments.count_by_company(company.id) > 0:
            raise ConflictError(
                "Company has departments and cannot be deleted; remove departments first"
            )
        self.companies.delete(company)
