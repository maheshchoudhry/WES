"""Audit + security-event logging (WP5)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.security import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        action: str,
        *,
        actor: str | None = None,
        category: str = "action",
        entity_type: str | None = None,
        entity_id: str | None = None,
        ip: str | None = None,
        severity: str = "info",
        detail: str | None = None,
    ) -> AuditLog:
        row = AuditLog(
            action=action,
            actor=actor,
            category=category,
            entity_type=entity_type,
            entity_id=entity_id,
            ip=ip,
            severity=severity,
            detail=detail,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def security_event(self, action: str, **kw) -> AuditLog:
        kw.setdefault("severity", "warning")
        return self.record(action, category="security", **kw)

    def list(
        self, *, category: str | None = None, limit: int = 200
    ) -> list[dict]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        if category:
            stmt = (
                select(AuditLog)
                .where(AuditLog.category == category)
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
            )
        return [self.serialize(r) for r in self.db.scalars(stmt).all()]

    @staticmethod
    def committed(action: str, **kw) -> None:
        """Record an audit event in its own committed transaction — used on
        request-failure paths (e.g. failed login) where the request session is
        rolled back."""
        try:
            from app.core.database import SessionLocal

            db = SessionLocal()
            try:
                AuditService(db).record(action, **kw)
                db.commit()
            finally:
                db.close()
        except Exception:  # pragma: no cover - never break the response path
            pass

    @staticmethod
    def serialize(r: AuditLog) -> dict:
        return {
            "id": str(r.id),
            "action": r.action,
            "actor": r.actor,
            "category": r.category,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "ip": r.ip,
            "severity": r.severity,
            "detail": r.detail,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
