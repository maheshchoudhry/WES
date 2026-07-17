"""Persistent long-term memory model (WP8)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, Base, UUIDPrimaryKeyMixin


class AgentMemory(UUIDPrimaryKeyMixin, Base):
    """A durable, retrievable piece of experience. Scoped to an employee, a
    project, or the whole org; recalled to inform future work."""

    __tablename__ = "agent_memories"

    scope: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    employee_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(400), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_task_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
