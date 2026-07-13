"""AI Company Core ORM models (Sprint 06).

Models the AI organization as first-class entities: AI departments, roles,
capabilities, employees (with self-referential reporting), plus per-employee
responsibilities and KPIs. Reuses the Company Engine base (portable UUID PK +
timestamps). Kept in one module for cohesion.
"""

import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.ai_enums import AIDecisionAuthority, AIEmployeeStatus, AIRoleLevel
from app.domain.enums import EntityStatus
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin

# Many-to-many: an AI employee has many capabilities; a capability is reused.
ai_employee_capabilities = Table(
    "ai_employee_capabilities",
    Base.metadata,
    Column(
        "ai_employee_id",
        GUID(),
        ForeignKey("ai_employees.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "ai_capability_id",
        GUID(),
        ForeignKey("ai_capabilities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class AIDepartment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_departments"

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    focus: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[EntityStatus] = mapped_column(
        String(20), nullable=False, default=EntityStatus.ACTIVE
    )


class AIRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_roles"

    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    level: Mapped[AIRoleLevel] = mapped_column(
        String(20), nullable=False, default=AIRoleLevel.OPERATIONAL
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Only the CEO role may have an employee without a reporting manager.
    is_executive_head: Mapped[bool] = mapped_column(default=False)


class AICapability(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_capabilities"

    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class AIEmployee(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_employees"

    employee_code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)

    department_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_roles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )

    authority: Mapped[AIDecisionAuthority] = mapped_column(
        String(20), nullable=False, default=AIDecisionAuthority.OPERATIONAL
    )
    decision_scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AIEmployeeStatus] = mapped_column(
        String(20), nullable=False, default=AIEmployeeStatus.ACTIVE
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Soft delete only (business rule): rows are never physically removed.
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    department: Mapped["AIDepartment"] = relationship()
    role: Mapped["AIRole"] = relationship()
    manager: Mapped["AIEmployee | None"] = relationship(remote_side="AIEmployee.id")
    responsibilities: Mapped[list["AIResponsibility"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="AIResponsibility.position",
    )
    kpis: Mapped[list["AIKPI"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    capabilities: Mapped[list["AICapability"]] = relationship(secondary=ai_employee_capabilities)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<AIEmployee {self.employee_code} {self.name!r}>"


class AIResponsibility(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_responsibilities"

    ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    employee: Mapped["AIEmployee"] = relationship(back_populates="responsibilities")


class AIKPI(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_kpis"

    ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    target: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(60), nullable=True)

    employee: Mapped["AIEmployee"] = relationship(back_populates="kpis")
