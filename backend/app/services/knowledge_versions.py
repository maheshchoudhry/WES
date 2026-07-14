"""Version and Review/Approval services for knowledge documents.

Every content change snapshots a ``knowledge_versions`` row (written by
KnowledgeService); this module reads that history and restores prior versions.
Reviews record an approval decision and drive the document lifecycle status.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.knowledge_enums import AccessAction, KnowledgeStatus, ReviewDecision
from app.models.knowledge import (
    KnowledgeAccessLog,
    KnowledgeDocument,
    KnowledgeReview,
    KnowledgeVersion,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class VersionService:
    def __init__(self, db: Session):
        self.db = db

    def history(self, document_id: uuid.UUID) -> list[KnowledgeVersion]:
        return list(
            self.db.scalars(
                select(KnowledgeVersion)
                .where(KnowledgeVersion.document_id == document_id)
                .order_by(KnowledgeVersion.version.desc())
            ).all()
        )

    def get_version(self, document_id: uuid.UUID, version: int) -> KnowledgeVersion:
        v = self.db.scalar(
            select(KnowledgeVersion).where(
                KnowledgeVersion.document_id == document_id,
                KnowledgeVersion.version == version,
            )
        )
        if v is None:
            raise NotFoundError(f"Version {version} of document {document_id} not found")
        return v

    def restore(self, document_id: uuid.UUID, version: int) -> KnowledgeDocument:
        """Restore a prior version as a new current version (non-destructive)."""
        doc = self.db.get(KnowledgeDocument, document_id)
        if doc is None:
            raise NotFoundError(f"Document {document_id} not found")
        target = self.get_version(document_id, version)
        doc.title = target.title
        doc.content = target.content
        doc.version += 1
        self.db.add(
            KnowledgeVersion(
                document_id=doc.id,
                version=doc.version,
                title=doc.title,
                content=doc.content,
                change_summary=f"Restored from v{version}",
                status=doc.status.value if hasattr(doc.status, "value") else doc.status,
                author_id=doc.author_id,
            )
        )
        self.db.flush()
        return doc

    def serialize(self, v: KnowledgeVersion) -> dict:
        return {
            "id": str(v.id),
            "document_id": str(v.document_id),
            "version": v.version,
            "title": v.title,
            "change_summary": v.change_summary,
            "status": v.status.value if hasattr(v.status, "value") else v.status,
            "author_id": str(v.author_id) if v.author_id else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }


class ApprovalService:
    """Knowledge reviews + approval workflow (drives document status)."""

    def __init__(self, db: Session, actor: str = "System"):
        self.db = db
        self.actor = actor

    def _doc(self, document_id: uuid.UUID) -> KnowledgeDocument:
        d = self.db.get(KnowledgeDocument, document_id)
        if d is None:
            raise NotFoundError(f"Document {document_id} not found")
        return d

    def submit_for_review(self, document_id: uuid.UUID) -> KnowledgeDocument:
        doc = self._doc(document_id)
        doc.status = KnowledgeStatus.IN_REVIEW
        self.db.flush()
        return doc

    def review(
        self,
        document_id: uuid.UUID,
        decision: ReviewDecision | str,
        *,
        reviewer_id: uuid.UUID | None = None,
        comment: str | None = None,
    ) -> KnowledgeReview:
        doc = self._doc(document_id)
        dec = decision.value if isinstance(decision, ReviewDecision) else decision
        review = KnowledgeReview(
            document_id=document_id,
            reviewer_id=reviewer_id,
            reviewer_name=self.actor,
            decision=dec,
            comment=comment,
        )
        self.db.add(review)
        # Drive the lifecycle status from the decision.
        if dec == ReviewDecision.APPROVED.value:
            doc.status = KnowledgeStatus.APPROVED
            doc.approver_id = reviewer_id
            doc.approved_at = _now()
        elif dec == ReviewDecision.CHANGES_REQUESTED.value:
            doc.status = KnowledgeStatus.DRAFT
        elif dec == ReviewDecision.REJECTED.value:
            doc.status = KnowledgeStatus.DRAFT
        self.db.add(
            KnowledgeAccessLog(
                document_id=document_id, actor=self.actor, action=AccessAction.APPROVE.value
            )
        )
        self.db.flush()
        return review

    def reviews_for(self, document_id: uuid.UUID) -> list[KnowledgeReview]:
        return list(
            self.db.scalars(
                select(KnowledgeReview)
                .where(KnowledgeReview.document_id == document_id)
                .order_by(KnowledgeReview.reviewed_at.desc())
            ).all()
        )

    def pending_reviews(self) -> list[KnowledgeDocument]:
        return list(
            self.db.scalars(
                select(KnowledgeDocument)
                .where(KnowledgeDocument.status == KnowledgeStatus.IN_REVIEW)
                .order_by(KnowledgeDocument.updated_at.desc())
            ).all()
        )

    def serialize(self, r: KnowledgeReview) -> dict:
        return {
            "id": str(r.id),
            "document_id": str(r.document_id),
            "reviewer_id": str(r.reviewer_id) if r.reviewer_id else None,
            "reviewer_name": r.reviewer_name,
            "decision": r.decision.value if hasattr(r.decision, "value") else r.decision,
            "comment": r.comment,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        }
