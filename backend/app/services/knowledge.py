"""Knowledge, Category, and Tag services.

Owns knowledge_documents, knowledge_categories, and knowledge_tags. Document
writes snapshot a version and record an access-log entry so history and analytics
stay accurate. This is the single source of truth for organizational knowledge.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.knowledge_enums import (
    AccessAction,
    DocumentType,
    KnowledgeStatus,
)
from app.models.knowledge import (
    KnowledgeAccessLog,
    KnowledgeCategory,
    KnowledgeDocument,
    KnowledgeEmbeddingPlaceholder,
    KnowledgeTag,
    KnowledgeVersion,
)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-") or "document"


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def list_categories(self) -> list[KnowledgeCategory]:
        return list(
            self.db.scalars(
                select(KnowledgeCategory).order_by(
                    KnowledgeCategory.position, KnowledgeCategory.name
                )
            ).all()
        )

    def get(self, category_id: uuid.UUID) -> KnowledgeCategory:
        c = self.db.get(KnowledgeCategory, category_id)
        if c is None:
            raise NotFoundError(f"Category {category_id} not found")
        return c

    def get_by_code(self, code: str) -> KnowledgeCategory | None:
        return self.db.scalar(select(KnowledgeCategory).where(KnowledgeCategory.code == code))

    def create(
        self, code: str, name: str, description: str | None = None, position: int = 0
    ) -> KnowledgeCategory:
        if self.get_by_code(code):
            raise ConflictError(f"Category '{code}' already exists")
        c = KnowledgeCategory(code=code, name=name, description=description, position=position)
        self.db.add(c)
        self.db.flush()
        return c

    def serialize(self, c: KnowledgeCategory, document_count: int | None = None) -> dict:
        return {
            "id": str(c.id),
            "code": c.code,
            "name": c.name,
            "description": c.description,
            "parent_id": str(c.parent_id) if c.parent_id else None,
            "position": c.position,
            "document_count": document_count,
        }

    def with_counts(self) -> list[dict]:
        counts = dict(
            self.db.execute(
                select(KnowledgeDocument.category_id, func.count(KnowledgeDocument.id)).group_by(
                    KnowledgeDocument.category_id
                )
            ).all()
        )
        return [self.serialize(c, counts.get(c.id, 0)) for c in self.list_categories()]


class TagService:
    def __init__(self, db: Session):
        self.db = db

    def list_tags(self) -> list[KnowledgeTag]:
        return list(self.db.scalars(select(KnowledgeTag).order_by(KnowledgeTag.label)).all())

    def get_or_create(self, label: str) -> KnowledgeTag:
        slug = slugify(label)
        tag = self.db.scalar(select(KnowledgeTag).where(KnowledgeTag.slug == slug))
        if tag is None:
            tag = KnowledgeTag(slug=slug, label=label)
            self.db.add(tag)
            self.db.flush()
        return tag

    def serialize(self, t: KnowledgeTag) -> dict:
        return {"id": str(t.id), "slug": t.slug, "label": t.label}


class KnowledgeService:
    """Documents CRUD + serialization + access logging."""

    def __init__(self, db: Session, actor: str = "System"):
        self.db = db
        self.actor = actor
        self.tags = TagService(db)
        self.categories = CategoryService(db)

    # -- reads -------------------------------------------------------------

    def list_documents(
        self,
        *,
        category_id: uuid.UUID | None = None,
        doc_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.updated_at.desc())
        if category_id is not None:
            stmt = stmt.where(KnowledgeDocument.category_id == category_id)
        if doc_type:
            stmt = stmt.where(KnowledgeDocument.doc_type == doc_type)
        if status:
            stmt = stmt.where(KnowledgeDocument.status == status)
        return list(self.db.scalars(stmt.limit(limit)).all())

    def get(self, document_id: uuid.UUID) -> KnowledgeDocument:
        d = self.db.get(KnowledgeDocument, document_id)
        if d is None:
            raise NotFoundError(f"Document {document_id} not found")
        return d

    def get_by_code(self, code: str) -> KnowledgeDocument | None:
        return self.db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.code == code))

    def view(self, document_id: uuid.UUID) -> KnowledgeDocument:
        """Fetch a document and record a view (increments the counter)."""
        d = self.get(document_id)
        d.view_count += 1
        self._log(d.id, AccessAction.VIEW)
        self.db.flush()
        return d

    def recent(self, limit: int = 8) -> list[KnowledgeDocument]:
        return list(
            self.db.scalars(
                select(KnowledgeDocument).order_by(KnowledgeDocument.updated_at.desc()).limit(limit)
            ).all()
        )

    def most_used(self, limit: int = 8) -> list[KnowledgeDocument]:
        return list(
            self.db.scalars(
                select(KnowledgeDocument)
                .order_by(KnowledgeDocument.view_count.desc(), KnowledgeDocument.updated_at.desc())
                .limit(limit)
            ).all()
        )

    # -- writes ------------------------------------------------------------

    def _next_code(self) -> str:
        n = self.db.scalar(select(func.count(KnowledgeDocument.id))) or 0
        return f"KB-{n + 1:04d}"

    def create(
        self,
        *,
        title: str,
        doc_type: DocumentType | str,
        content: str = "",
        summary: str | None = None,
        category_id: uuid.UUID | None = None,
        keywords: str | None = None,
        author_id: uuid.UUID | None = None,
        owner_ai_employee_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        code: str | None = None,
        status: KnowledgeStatus | str = KnowledgeStatus.DRAFT,
    ) -> KnowledgeDocument:
        dt = doc_type.value if isinstance(doc_type, DocumentType) else doc_type
        if dt not in {t.value for t in DocumentType}:
            raise ValidationError(f"Unknown document type '{dt}'")
        code = code or self._next_code()
        if self.get_by_code(code):
            raise ConflictError(f"Document '{code}' already exists")
        if category_id is not None:
            self.categories.get(category_id)  # validates existence
        doc = KnowledgeDocument(
            code=code,
            slug=slugify(title),
            title=title,
            doc_type=dt,
            category_id=category_id,
            summary=summary,
            content=content,
            keywords=keywords,
            author_id=author_id,
            owner_ai_employee_id=owner_ai_employee_id,
            status=status.value if isinstance(status, KnowledgeStatus) else status,
            version=1,
        )
        for label in tags or []:
            doc.tags.append(self.tags.get_or_create(label))
        self.db.add(doc)
        self.db.flush()
        self._snapshot(doc, "Initial version")
        # Register the document for future vectorization (no vectors stored).
        self.db.add(
            KnowledgeEmbeddingPlaceholder(
                document_id=doc.id, status="pending", note="Awaiting semantic-search backend"
            )
        )
        self._log(doc.id, AccessAction.CREATE)
        self.db.flush()
        return doc

    def update(
        self,
        document_id: uuid.UUID,
        *,
        title: str | None = None,
        content: str | None = None,
        summary: str | None = None,
        category_id: uuid.UUID | None = None,
        keywords: str | None = None,
        tags: list[str] | None = None,
        change_summary: str | None = None,
    ) -> KnowledgeDocument:
        doc = self.get(document_id)
        content_changed = False
        if title is not None:
            doc.title = title
            doc.slug = slugify(title)
        if content is not None and content != doc.content:
            doc.content = content
            content_changed = True
        if summary is not None:
            doc.summary = summary
        if category_id is not None:
            self.categories.get(category_id)
            doc.category_id = category_id
        if keywords is not None:
            doc.keywords = keywords
        if tags is not None:
            doc.tags = [self.tags.get_or_create(label) for label in tags]
        # A new version is snapshotted whenever content changes.
        if content_changed or title is not None:
            doc.version += 1
            self._snapshot(doc, change_summary or "Updated document")
        self._log(doc.id, AccessAction.UPDATE)
        self.db.flush()
        return doc

    def _snapshot(self, doc: KnowledgeDocument, change_summary: str) -> None:
        self.db.add(
            KnowledgeVersion(
                document_id=doc.id,
                version=doc.version,
                title=doc.title,
                content=doc.content,
                change_summary=change_summary,
                status=doc.status.value if hasattr(doc.status, "value") else doc.status,
                author_id=doc.author_id,
            )
        )

    def _log(self, document_id: uuid.UUID, action: AccessAction) -> None:
        self.db.add(
            KnowledgeAccessLog(document_id=document_id, actor=self.actor, action=action.value)
        )

    # -- serialization -----------------------------------------------------

    def serialize(self, d: KnowledgeDocument, *, full: bool = False) -> dict:
        base = {
            "id": str(d.id),
            "code": d.code,
            "slug": d.slug,
            "title": d.title,
            "doc_type": d.doc_type.value if hasattr(d.doc_type, "value") else d.doc_type,
            "category_id": str(d.category_id) if d.category_id else None,
            "category_name": d.category.name if d.category else None,
            "summary": d.summary,
            "status": d.status.value if hasattr(d.status, "value") else d.status,
            "version": d.version,
            "tags": [t.label for t in d.tags],
            "is_pinned": d.is_pinned,
            "view_count": d.view_count,
            "author_id": str(d.author_id) if d.author_id else None,
            "approver_id": str(d.approver_id) if d.approver_id else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        if full:
            base["content"] = d.content
            base["keywords"] = d.keywords
            base["approved_at"] = d.approved_at.isoformat() if d.approved_at else None
            base["review_date"] = d.review_date.isoformat() if d.review_date else None
        return base
