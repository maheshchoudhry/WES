"""Persistent long-term memory (WP8).

AI employees, projects, and the org accumulate durable experience — what was
implemented, what was decided, lessons learned. Memories live in the database, so
they survive restarts, and are recalled (keyword + recency) to inform future work.
Deterministic today; when a live provider is configured (WP2), recall can feed the
prompt without changing this contract.
"""

from __future__ import annotations

import json
import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import AgentMemory

_STOP = {"a", "an", "the", "to", "on", "for", "of", "and", "add", "new", "with"}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in _STOP and len(t) > 2}


class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def remember(
        self,
        *,
        scope: str,
        kind: str,
        summary: str,
        content: str | None = None,
        employee_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        source_task_id: uuid.UUID | None = None,
    ) -> AgentMemory:
        m = AgentMemory(
            scope=scope,
            kind=kind,
            summary=summary[:400],
            content=content,
            employee_id=employee_id,
            project_id=project_id,
            tags=json.dumps(tags or []),
            source_task_id=source_task_id,
        )
        self.db.add(m)
        self.db.flush()
        return m

    def recall(
        self,
        query: str = "",
        *,
        scope: str | None = None,
        employee_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        kind: str | None = None,
        limit: int = 8,
    ) -> list[dict]:
        stmt = select(AgentMemory)
        if scope:
            stmt = stmt.where(AgentMemory.scope == scope)
        if employee_id:
            stmt = stmt.where(AgentMemory.employee_id == employee_id)
        if project_id:
            stmt = stmt.where(AgentMemory.project_id == project_id)
        if kind:
            stmt = stmt.where(AgentMemory.kind == kind)
        rows = self.db.scalars(stmt.order_by(AgentMemory.created_at.desc()).limit(200)).all()

        qtokens = _tokens(query)
        scored = []
        for m in rows:
            hay = _tokens(f"{m.summary} {m.content or ''} {m.tags or ''}")
            overlap = len(qtokens & hay) if qtokens else 0
            # Keyword-relevant first; otherwise most-recent (already ordered).
            scored.append((overlap, m))
        if qtokens:
            scored = [s for s in scored if s[0] > 0] or scored
            scored.sort(key=lambda s: s[0], reverse=True)
        return [self.serialize(m) for _, m in scored[:limit]]

    def list_for_employee(self, employee_id: uuid.UUID, limit: int = 20) -> list[dict]:
        rows = self.db.scalars(
            select(AgentMemory)
            .where(AgentMemory.employee_id == employee_id)
            .order_by(AgentMemory.created_at.desc())
            .limit(limit)
        ).all()
        return [self.serialize(m) for m in rows]

    @staticmethod
    def serialize(m: AgentMemory) -> dict:
        return {
            "id": str(m.id),
            "scope": m.scope,
            "kind": m.kind,
            "summary": m.summary,
            "content": m.content,
            "tags": json.loads(m.tags) if m.tags else [],
            "employee_id": str(m.employee_id) if m.employee_id else None,
            "project_id": str(m.project_id) if m.project_id else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
