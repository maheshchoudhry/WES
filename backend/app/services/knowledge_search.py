"""Search and AI Retrieval services.

SearchService provides keyword / full-text / category / tag / relationship search
over the knowledge base. It is deliberately backend-agnostic: today it runs SQL
``LIKE`` matching, but the ``search`` entry point and result shape are designed so
a vector/semantic backend can be dropped in later without changing callers or the
public API. The ``knowledge_embeddings_placeholder`` table reserves that seam.

RetrievalService is the AI-facing entry point: given an AI employee and an
optional work item, it returns the relevant documents, SOPs, ADRs, standards,
previous decisions, references, and templates that must be retrieved *before*
execution.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.knowledge_enums import AccessAction, DocumentType, KnowledgeStatus
from app.models.knowledge import (
    KnowledgeAccessLog,
    KnowledgeDocument,
    KnowledgeReference,
    KnowledgeTag,
    knowledge_document_tags,
)

# Document types most relevant to AI execution, grouped by the context slot they
# fill. The mapping is data, not branching on any provider or model.
_STANDARD_TYPES = (DocumentType.CODING_STANDARD.value, DocumentType.SECURITY_STANDARD.value)


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def _match(self, stmt, query: str):
        like = f"%{query.lower()}%"
        return stmt.where(
            or_(
                func.lower(KnowledgeDocument.title).like(like),
                func.lower(KnowledgeDocument.summary).like(like),
                func.lower(KnowledgeDocument.content).like(like),
                func.lower(KnowledgeDocument.keywords).like(like),
                func.lower(KnowledgeDocument.code).like(like),
            )
        )

    def search(
        self,
        query: str | None = None,
        *,
        category_id: uuid.UUID | None = None,
        doc_type: str | None = None,
        tag: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[KnowledgeDocument]:
        """Unified search entry point (keyword + full-text + filters).

        A future semantic backend can replace the LIKE matching here while keeping
        this signature and return type identical.
        """
        stmt = select(KnowledgeDocument)
        if query:
            stmt = self._match(stmt, query)
        if category_id is not None:
            stmt = stmt.where(KnowledgeDocument.category_id == category_id)
        if doc_type:
            stmt = stmt.where(KnowledgeDocument.doc_type == doc_type)
        if status:
            stmt = stmt.where(KnowledgeDocument.status == status)
        if tag:
            stmt = (
                stmt.join(
                    knowledge_document_tags,
                    knowledge_document_tags.c.document_id == KnowledgeDocument.id,
                )
                .join(KnowledgeTag, KnowledgeTag.id == knowledge_document_tags.c.tag_id)
                .where(or_(KnowledgeTag.slug == tag, KnowledgeTag.label == tag))
            )
        stmt = stmt.order_by(KnowledgeDocument.updated_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())


class RetrievalService:
    """AI knowledge retrieval — assembled before every AI execution."""

    def __init__(self, db: Session):
        self.db = db
        self.search = SearchService(db)

    def _by_types(
        self, types: tuple[str, ...], *, approved_only: bool = True, limit: int = 5
    ) -> list[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.doc_type.in_(types))
        if approved_only:
            stmt = stmt.where(KnowledgeDocument.status == KnowledgeStatus.APPROVED)
        return list(
            self.db.scalars(stmt.order_by(KnowledgeDocument.view_count.desc()).limit(limit)).all()
        )

    def retrieve_for(
        self,
        *,
        keywords: str | None = None,
        ai_employee_id: uuid.UUID | None = None,
        limit: int = 5,
        log: bool = True,
    ) -> dict:
        """Return the knowledge bundle an AI employee must consume before executing.

        Slots: relevant_documents, relevant_sop, relevant_adr, relevant_standards,
        relevant_decisions, relevant_references, relevant_templates.
        """
        relevant = self.search.search(keywords, limit=limit) if keywords else []
        sops = self._by_types((DocumentType.SOP.value,), approved_only=False, limit=limit)
        adrs = self._by_types((DocumentType.ADR.value,), approved_only=False, limit=limit)
        standards = self._by_types(_STANDARD_TYPES, approved_only=False, limit=limit)
        decisions = self._by_types(
            (DocumentType.LESSONS_LEARNED.value,), approved_only=False, limit=limit
        )
        templates = self._by_types((DocumentType.TEMPLATE.value,), approved_only=False, limit=limit)

        bundle_ids = {d.id for d in relevant + sops + adrs + standards + decisions + templates}
        references: list[KnowledgeReference] = []
        if bundle_ids:
            references = list(
                self.db.scalars(
                    select(KnowledgeReference).where(KnowledgeReference.document_id.in_(bundle_ids))
                ).all()
            )
        if log:
            for did in bundle_ids:
                self.db.add(
                    KnowledgeAccessLog(
                        document_id=did,
                        ai_employee_id=ai_employee_id,
                        action=AccessAction.RETRIEVE.value,
                        context="pre-execution retrieval",
                    )
                )
            self.db.flush()

        def _brief(d: KnowledgeDocument) -> dict:
            return {
                "id": str(d.id),
                "code": d.code,
                "title": d.title,
                "doc_type": d.doc_type.value if hasattr(d.doc_type, "value") else d.doc_type,
                "summary": d.summary,
            }

        return {
            "relevant_documents": [_brief(d) for d in relevant],
            "relevant_sop": [_brief(d) for d in sops],
            "relevant_adr": [_brief(d) for d in adrs],
            "relevant_standards": [_brief(d) for d in standards],
            "relevant_decisions": [_brief(d) for d in decisions],
            "relevant_templates": [_brief(d) for d in templates],
            "relevant_references": [
                {
                    "document_id": str(r.document_id),
                    "entity_type": (
                        r.entity_type.value if hasattr(r.entity_type, "value") else r.entity_type
                    ),
                    "label": r.label,
                }
                for r in references
            ],
        }
