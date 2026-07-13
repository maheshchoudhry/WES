"""Company business logic."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.company import Company
from app.repositories.company import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.services.exceptions import NotFoundError


class CompanyService:
    def __init__(self, db: Session) -> None:
        self.repo = CompanyRepository(db)

    def list(self, offset: int, limit: int) -> tuple[list[Company], int]:
        return self.repo.list(offset, limit), self.repo.count()

    def get(self, company_id: int) -> Company:
        obj = self.repo.get(company_id)
        if obj is None:
            raise NotFoundError("Company not found", {"id": company_id})
        return obj

    def create(self, data: CompanyCreate) -> Company:
        return self.repo.save(Company(**data.model_dump()))

    def update(self, company_id: int, data: CompanyUpdate) -> Company:
        obj = self.get(company_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        return self.repo.save(obj)

    def delete(self, company_id: int) -> None:
        self.repo.delete(self.get(company_id))
