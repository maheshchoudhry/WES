"""Employee ORM model.

An Employee belongs to a Company and is optionally assigned to a Department. An
employee may report to another employee (self-referential hierarchy), mirroring
the WES Reporting Hierarchy.
"""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import AuthorityLevel, EmployeeStatus
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class Employee(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "employees"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reports_to_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )

    employee_code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    position: Mapped[str] = mapped_column(String(160), nullable=False)
    authority: Mapped[AuthorityLevel] = mapped_column(
        String(20), nullable=False, default=AuthorityLevel.OPERATIONAL
    )
    status: Mapped[EmployeeStatus] = mapped_column(
        String(20), nullable=False, default=EmployeeStatus.ONBOARDING
    )

    company: Mapped["Company"] = relationship()  # noqa: F821
    department: Mapped["Department | None"] = relationship(  # noqa: F821
        back_populates="employees"
    )
    manager: Mapped["Employee | None"] = relationship(remote_side="Employee.id")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Employee {self.employee_code} {self.full_name!r}>"
