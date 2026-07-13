"""Generic repository base.

Repositories encapsulate all database access for an aggregate. Services depend
on repositories, never on the ORM session directly, keeping persistence details
in one place (layered architecture frozen in Sprint 01).
"""

import uuid
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get(self, entity_id: uuid.UUID) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(self.model)) or 0)

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.flush()
