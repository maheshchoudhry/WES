"""Department ORM model.

A Department belongs to exactly one Company. Its ``code`` is unique within that
company. Employees are assigned to departments.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import EntityStatus
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class Department(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_department_company_code"),
        UniqueConstraint("company_id", "name", name="uq_department_company_name"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    focus: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[EntityStatus] = mapped_column(
        String(20), nullable=False, default=EntityStatus.ACTIVE
    )

    company: Mapped["Company"] = relationship(back_populates="departments")  # noqa: F821
    employees: Mapped[list["Employee"]] = relationship(back_populates="department")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Department {self.code} {self.name!r}>"
