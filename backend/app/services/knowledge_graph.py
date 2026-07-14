"""Knowledge Graph services: Relationship and Reference.

Relationships link documents to each other; references link documents to
organizational entities (projects, employees, AI employees, tasks, SOPs,
architecture, repositories, standards, decision records). Both are queryable so
the graph can be traversed from any document.
"""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.knowledge_enums import ReferenceEntityType, RelationshipType
from app.models.knowledge import (
    KnowledgeDocument,
    KnowledgeReference,
    KnowledgeRelationship,
)


class RelationshipService:
    def __init__(self, db: Session):
        self.db = db

    def _doc(self, document_id: uuid.UUID) -> KnowledgeDocument:
        d = self.db.get(KnowledgeDocument, document_id)
        if d is None:
            raise NotFoundError(f"Document {document_id} not found")
        return d

    def link(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        relationship_type: RelationshipType | str,
        note: str | None = None,
    ) -> KnowledgeRelationship:
        if source_id == target_id:
            raise ValidationError("A document cannot be related to itself")
        self._doc(source_id)
        self._doc(target_id)
        rt = (
            relationship_type.value
            if isinstance(relationship_type, RelationshipType)
            else relationship_type
        )
        if rt not in {r.value for r in RelationshipType}:
            raise ValidationError(f"Unknown relationship type '{rt}'")
        existing = self.db.scalar(
            select(KnowledgeRelationship).where(
                KnowledgeRelationship.source_document_id == source_id,
                KnowledgeRelationship.target_document_id == target_id,
                KnowledgeRelationship.relationship_type == rt,
            )
        )
        if existing is not None:
            return existing
        rel = KnowledgeRelationship(
            source_document_id=source_id,
            target_document_id=target_id,
            relationship_type=rt,
            note=note,
        )
        self.db.add(rel)
        self.db.flush()
        return rel

    def unlink(self, relationship_id: uuid.UUID) -> None:
        rel = self.db.get(KnowledgeRelationship, relationship_id)
        if rel is None:
            raise NotFoundError(f"Relationship {relationship_id} not found")
        self.db.delete(rel)
        self.db.flush()

    def for_document(self, document_id: uuid.UUID) -> list[KnowledgeRelationship]:
        """All relationships where the document is the source or the target."""
        return list(
            self.db.scalars(
                select(KnowledgeRelationship).where(
                    or_(
                        KnowledgeRelationship.source_document_id == document_id,
                        KnowledgeRelationship.target_document_id == document_id,
                    )
                )
            ).all()
        )

    def related_documents(self, document_id: uuid.UUID) -> list[KnowledgeDocument]:
        rels = self.for_document(document_id)
        ids = set()
        for r in rels:
            ids.add(
                r.target_document_id
                if r.source_document_id == document_id
                else r.source_document_id
            )
        if not ids:
            return []
        return list(
            self.db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.id.in_(ids))).all()
        )

    def serialize(self, r: KnowledgeRelationship) -> dict:
        titles = dict(
            self.db.execute(
                select(KnowledgeDocument.id, KnowledgeDocument.title).where(
                    KnowledgeDocument.id.in_([r.source_document_id, r.target_document_id])
                )
            ).all()
        )
        return {
            "id": str(r.id),
            "source_document_id": str(r.source_document_id),
            "source_title": titles.get(r.source_document_id),
            "target_document_id": str(r.target_document_id),
            "target_title": titles.get(r.target_document_id),
            "relationship_type": (
                r.relationship_type.value
                if hasattr(r.relationship_type, "value")
                else r.relationship_type
            ),
            "note": r.note,
        }

    def graph(self, limit: int = 200) -> dict:
        """Node/edge representation of the whole document graph (for visualization)."""
        docs = list(self.db.scalars(select(KnowledgeDocument).limit(limit)).all())
        rels = list(self.db.scalars(select(KnowledgeRelationship)).all())
        doc_ids = {d.id for d in docs}
        nodes = [
            {
                "id": str(d.id),
                "code": d.code,
                "title": d.title,
                "doc_type": d.doc_type.value if hasattr(d.doc_type, "value") else d.doc_type,
                "category_id": str(d.category_id) if d.category_id else None,
            }
            for d in docs
        ]
        edges = [
            {
                "id": str(r.id),
                "source": str(r.source_document_id),
                "target": str(r.target_document_id),
                "type": (
                    r.relationship_type.value
                    if hasattr(r.relationship_type, "value")
                    else r.relationship_type
                ),
            }
            for r in rels
            if r.source_document_id in doc_ids and r.target_document_id in doc_ids
        ]
        return {"nodes": nodes, "edges": edges}


class ReferenceService:
    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        document_id: uuid.UUID,
        entity_type: ReferenceEntityType | str,
        entity_id: uuid.UUID | None = None,
        label: str | None = None,
    ) -> KnowledgeReference:
        if self.db.get(KnowledgeDocument, document_id) is None:
            raise NotFoundError(f"Document {document_id} not found")
        et = entity_type.value if isinstance(entity_type, ReferenceEntityType) else entity_type
        if et not in {e.value for e in ReferenceEntityType}:
            raise ValidationError(f"Unknown reference entity type '{et}'")
        ref = KnowledgeReference(
            document_id=document_id, entity_type=et, entity_id=entity_id, label=label
        )
        self.db.add(ref)
        self.db.flush()
        return ref

    def for_document(self, document_id: uuid.UUID) -> list[KnowledgeReference]:
        return list(
            self.db.scalars(
                select(KnowledgeReference).where(KnowledgeReference.document_id == document_id)
            ).all()
        )

    def for_entity(self, entity_type: str, entity_id: uuid.UUID) -> list[KnowledgeReference]:
        return list(
            self.db.scalars(
                select(KnowledgeReference).where(
                    KnowledgeReference.entity_type == entity_type,
                    KnowledgeReference.entity_id == entity_id,
                )
            ).all()
        )

    def serialize(self, r: KnowledgeReference) -> dict:
        return {
            "id": str(r.id),
            "document_id": str(r.document_id),
            "entity_type": (
                r.entity_type.value if hasattr(r.entity_type, "value") else r.entity_type
            ),
            "entity_id": str(r.entity_id) if r.entity_id else None,
            "label": r.label,
        }
