"""Founder notification service (Phase 4)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.notifications import Notification


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        kind: str,
        title: str,
        message: str | None = None,
        severity: str = "info",
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> Notification:
        n = Notification(
            kind=kind,
            title=title,
            message=message,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self.db.add(n)
        self.db.flush()
        return n

    def list(self, *, unread_only: bool = False, limit: int = 100) -> list[dict]:
        stmt = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
        if unread_only:
            stmt = (
                select(Notification)
                .where(Notification.read.is_(False))
                .order_by(Notification.created_at.desc())
                .limit(limit)
            )
        return [self.serialize(n) for n in self.db.scalars(stmt).all()]

    def unread_count(self) -> int:
        return (
            self.db.scalar(
                select(func.count(Notification.id)).where(Notification.read.is_(False))
            )
            or 0
        )

    def mark_read(self, notification_id: uuid.UUID) -> dict:
        n = self.db.get(Notification, notification_id)
        if n is None:
            raise NotFoundError(f"Notification {notification_id} not found")
        n.read = True
        self.db.flush()
        return self.serialize(n)

    def mark_all_read(self) -> int:
        rows = self.db.scalars(
            select(Notification).where(Notification.read.is_(False))
        ).all()
        for n in rows:
            n.read = True
        self.db.flush()
        return len(rows)

    @staticmethod
    def serialize(n: Notification) -> dict:
        return {
            "id": str(n.id),
            "kind": n.kind,
            "title": n.title,
            "message": n.message,
            "severity": n.severity,
            "entity_type": n.entity_type,
            "entity_id": n.entity_id,
            "read": n.read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
