"""Security models (WP5): refresh-token registry + audit log."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, Base, UUIDPrimaryKeyMixin


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    """One row per issued refresh token (by ``jti``), enabling rotation +
    per-token revocation."""

    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Append-only trail of privileged actions and security events."""

    __tablename__ = "audit_log"

    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="action", index=True)
    entity_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
