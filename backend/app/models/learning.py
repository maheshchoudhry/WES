"""Self-learning rule model (WP9)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, Base, UUIDPrimaryKeyMixin


class LearningRule(UUIDPrimaryKeyMixin, Base):
    """A reusable rule derived from completed work. ``occurrences`` grows as the
    same lesson recurs; ``applied_count`` grows each time it informs a new task."""

    __tablename__ = "learning_rules"

    kind: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    rule: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    dimension: Mapped[str | None] = mapped_column(String(40), nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    applied_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_task_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
