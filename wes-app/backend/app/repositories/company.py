"""Company repository."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: Session) -> None:
        super().__init__(Company, db)
