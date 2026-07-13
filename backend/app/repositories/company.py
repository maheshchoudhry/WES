"""Company repository."""

from sqlalchemy import select

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    model = Company

    def get_by_slug(self, slug: str) -> Company | None:
        return self.db.scalar(select(Company).where(Company.slug == slug))

    def get_by_name(self, name: str) -> Company | None:
        return self.db.scalar(select(Company).where(Company.name == name))
