"""Knowledge Analytics service — founder & AI dashboards, ADR registry.

Aggregates statistics over the knowledge base: document/category counts, recent
and most-used documents, pending reviews, and a simple health signal. Also serves
the Architecture Decision Record registry (kept here as it is analytics-adjacent
and read-heavy)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.knowledge_enums import ADRStatus, KnowledgeStatus
from app.models.knowledge import (
    ArchitectureDecisionRecord,
    KnowledgeAccessLog,
    KnowledgeCategory,
    KnowledgeDocument,
)
from app.services.knowledge import KnowledgeService


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.knowledge = KnowledgeService(db)

    def _count(self, stmt) -> int:
        return self.db.scalar(stmt) or 0

    def statistics(self) -> dict:
        total = self._count(select(func.count(KnowledgeDocument.id)))
        by_status = dict(
            self.db.execute(
                select(KnowledgeDocument.status, func.count(KnowledgeDocument.id)).group_by(
                    KnowledgeDocument.status
                )
            ).all()
        )
        by_type = dict(
            self.db.execute(
                select(KnowledgeDocument.doc_type, func.count(KnowledgeDocument.id)).group_by(
                    KnowledgeDocument.doc_type
                )
            ).all()
        )

        def _key(v):
            return v.value if hasattr(v, "value") else v

        return {
            "total_documents": total,
            "total_categories": self._count(select(func.count(KnowledgeCategory.id))),
            "total_adrs": self._count(select(func.count(ArchitectureDecisionRecord.id))),
            "by_status": {_key(k): v for k, v in by_status.items()},
            "by_type": {_key(k): v for k, v in by_type.items()},
            "total_views": self._count(
                select(func.coalesce(func.sum(KnowledgeDocument.view_count), 0))
            ),
            "retrievals": self._count(
                select(func.count(KnowledgeAccessLog.id)).where(
                    KnowledgeAccessLog.action == "retrieve"
                )
            ),
        }

    def founder_dashboard(self) -> dict:
        stats = self.statistics()
        approved = stats["by_status"].get(KnowledgeStatus.APPROVED.value, 0)
        pending = stats["by_status"].get(KnowledgeStatus.IN_REVIEW.value, 0)
        total = stats["total_documents"] or 0
        # Health: share of documents that are approved (single source of truth quality).
        coverage = round(approved / total, 3) if total else 0.0
        health = "healthy" if coverage >= 0.5 else "attention" if total else "empty"
        return {
            "statistics": stats,
            "documents": total,
            "categories": stats["total_categories"],
            "pending_reviews": pending,
            "approved_documents": approved,
            "recent_knowledge": [self.knowledge.serialize(d) for d in self.knowledge.recent(6)],
            "most_used": [self.knowledge.serialize(d) for d in self.knowledge.most_used(6)],
            "knowledge_health": health,
            "approved_coverage": coverage,
        }

    def ai_dashboard(self, keywords: str | None = None) -> dict:
        """Knowledge surfaced to an AI employee: suggestions, references, standards."""
        from app.services.knowledge_search import RetrievalService

        bundle = RetrievalService(self.db).retrieve_for(keywords=keywords, log=False, limit=5)
        return {
            "suggested_knowledge": bundle["relevant_documents"],
            "recent_knowledge": [self.knowledge.serialize(d) for d in self.knowledge.recent(5)],
            "architecture_references": bundle["relevant_adr"],
            "coding_standards": bundle["relevant_standards"],
            "sop_recommendations": bundle["relevant_sop"],
            "organization_memory": bundle["relevant_decisions"],
            "related_documents": bundle["relevant_templates"],
        }


class ADRService:
    def __init__(self, db: Session):
        self.db = db

    def list_adrs(self) -> list[ArchitectureDecisionRecord]:
        return list(
            self.db.scalars(
                select(ArchitectureDecisionRecord).order_by(ArchitectureDecisionRecord.code)
            ).all()
        )

    def get(self, adr_id: uuid.UUID) -> ArchitectureDecisionRecord:
        a = self.db.get(ArchitectureDecisionRecord, adr_id)
        if a is None:
            raise NotFoundError(f"ADR {adr_id} not found")
        return a

    def _next_code(self) -> str:
        n = self.db.scalar(select(func.count(ArchitectureDecisionRecord.id))) or 0
        return f"ADR-{n + 1:04d}"

    def create(
        self,
        *,
        title: str,
        context: str | None = None,
        decision: str | None = None,
        consequences: str | None = None,
        status: ADRStatus | str = ADRStatus.PROPOSED,
        document_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        decided_by_id: uuid.UUID | None = None,
        code: str | None = None,
    ) -> ArchitectureDecisionRecord:
        code = code or self._next_code()
        if self.db.scalar(
            select(ArchitectureDecisionRecord).where(ArchitectureDecisionRecord.code == code)
        ):
            raise ConflictError(f"ADR '{code}' already exists")
        st = status.value if isinstance(status, ADRStatus) else status
        adr = ArchitectureDecisionRecord(
            code=code,
            title=title,
            context=context,
            decision=decision,
            consequences=consequences,
            status=st,
            document_id=document_id,
            project_id=project_id,
            decided_by_id=decided_by_id,
            decided_at=_now() if st == ADRStatus.ACCEPTED.value else None,
        )
        self.db.add(adr)
        self.db.flush()
        return adr

    def set_status(self, adr_id: uuid.UUID, status: ADRStatus | str) -> ArchitectureDecisionRecord:
        adr = self.get(adr_id)
        st = status.value if isinstance(status, ADRStatus) else status
        adr.status = st
        if st == ADRStatus.ACCEPTED.value and adr.decided_at is None:
            adr.decided_at = _now()
        self.db.flush()
        return adr

    def serialize(self, a: ArchitectureDecisionRecord) -> dict:
        return {
            "id": str(a.id),
            "code": a.code,
            "title": a.title,
            "status": a.status.value if hasattr(a.status, "value") else a.status,
            "context": a.context,
            "decision": a.decision,
            "consequences": a.consequences,
            "document_id": str(a.document_id) if a.document_id else None,
            "project_id": str(a.project_id) if a.project_id else None,
            "supersedes_adr_id": str(a.supersedes_adr_id) if a.supersedes_adr_id else None,
            "decided_at": a.decided_at.isoformat() if a.decided_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
