"""Company ORM model.

The Company is the root of the WES organization. Departments belong to a
company; employees belong (transitively) to a company through departments.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import EntityStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    company_type: Mapped[str] = mapped_column(String(120), nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[EntityStatus] = mapped_column(
        String(20), nullable=False, default=EntityStatus.ACTIVE
    )

    departments: Mapped[list["Department"]] = relationship(  # noqa: F821
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Company {self.name!r}>"
