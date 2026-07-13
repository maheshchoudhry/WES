"""Generic data-access repository."""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], db: Session) -> None:
        self.model = model
        self.db = db

    def get(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def list(self, offset: int = 0, limit: int = 50) -> list[ModelT]:
        stmt = select(self.model).order_by(self.model.id).offset(offset).limit(limit)
        return list(self.db.scalars(stmt))

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(self.model)) or 0

    def save(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.commit()
