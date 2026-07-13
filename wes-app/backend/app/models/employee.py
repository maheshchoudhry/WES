"""Employee ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.department import Department


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL")
    )
    reports_to: Mapped[str | None] = mapped_column(String(255))
    authority_level: Mapped[str] = mapped_column(
        String(80), default="Operational", nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    availability_status: Mapped[str] = mapped_column(
        String(50), default="available", nullable=False
    )
    operational_state: Mapped[str] = mapped_column(
        String(50), default="available", nullable=False
    )
    version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    department: Mapped["Department | None"] = relationship(
        back_populates="employees", lazy="joined"
    )
