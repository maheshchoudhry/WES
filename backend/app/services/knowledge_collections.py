"""Bookmark and Collection services.

Bookmarks are per-user favorites; collections are curated, ordered sets of
documents (owned by a user). Both read from the single knowledge source of truth.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.knowledge import (
    KnowledgeBookmark,
    KnowledgeCollection,
    KnowledgeCollectionItem,
    KnowledgeDocument,
)
from app.services.knowledge import slugify


class BookmarkService:
    def __init__(self, db: Session):
        self.db = db

    def _doc(self, document_id: uuid.UUID) -> KnowledgeDocument:
        d = self.db.get(KnowledgeDocument, document_id)
        if d is None:
            raise NotFoundError(f"Document {document_id} not found")
        return d

    def list_for_user(self, user_id: uuid.UUID) -> list[KnowledgeBookmark]:
        return list(
            self.db.scalars(
                select(KnowledgeBookmark)
                .where(KnowledgeBookmark.user_id == user_id)
                .order_by(KnowledgeBookmark.created_at.desc())
            ).all()
        )

    def add(
        self, user_id: uuid.UUID, document_id: uuid.UUID, note: str | None = None
    ) -> KnowledgeBookmark:
        self._doc(document_id)
        existing = self.db.scalar(
            select(KnowledgeBookmark).where(
                KnowledgeBookmark.user_id == user_id,
                KnowledgeBookmark.document_id == document_id,
            )
        )
        if existing is not None:
            return existing
        bm = KnowledgeBookmark(user_id=user_id, document_id=document_id, note=note)
        self.db.add(bm)
        self.db.flush()
        return bm

    def remove(self, user_id: uuid.UUID, document_id: uuid.UUID) -> None:
        bm = self.db.scalar(
            select(KnowledgeBookmark).where(
                KnowledgeBookmark.user_id == user_id,
                KnowledgeBookmark.document_id == document_id,
            )
        )
        if bm is not None:
            self.db.delete(bm)
            self.db.flush()

    def serialize(self, bm: KnowledgeBookmark) -> dict:
        doc = self.db.get(KnowledgeDocument, bm.document_id)
        return {
            "id": str(bm.id),
            "document_id": str(bm.document_id),
            "document_title": doc.title if doc else None,
            "document_code": doc.code if doc else None,
            "note": bm.note,
            "created_at": bm.created_at.isoformat() if bm.created_at else None,
        }


class CollectionService:
    def __init__(self, db: Session):
        self.db = db

    def list_collections(self) -> list[KnowledgeCollection]:
        return list(
            self.db.scalars(select(KnowledgeCollection).order_by(KnowledgeCollection.name)).all()
        )

    def get(self, collection_id: uuid.UUID) -> KnowledgeCollection:
        c = self.db.get(KnowledgeCollection, collection_id)
        if c is None:
            raise NotFoundError(f"Collection {collection_id} not found")
        return c

    def create(
        self,
        name: str,
        *,
        description: str | None = None,
        owner_id: uuid.UUID | None = None,
        slug: str | None = None,
    ) -> KnowledgeCollection:
        slug = slug or slugify(name)
        if self.db.scalar(select(KnowledgeCollection).where(KnowledgeCollection.slug == slug)):
            raise ConflictError(f"Collection '{slug}' already exists")
        c = KnowledgeCollection(slug=slug, name=name, description=description, owner_id=owner_id)
        self.db.add(c)
        self.db.flush()
        return c

    def add_document(self, collection_id: uuid.UUID, document_id: uuid.UUID) -> KnowledgeCollection:
        c = self.get(collection_id)
        if self.db.get(KnowledgeDocument, document_id) is None:
            raise NotFoundError(f"Document {document_id} not found")
        if any(i.document_id == document_id for i in c.items):
            return c
        position = len(c.items)
        self.db.add(
            KnowledgeCollectionItem(collection_id=c.id, document_id=document_id, position=position)
        )
        self.db.flush()
        self.db.refresh(c)
        return c

    def remove_document(self, collection_id: uuid.UUID, document_id: uuid.UUID) -> None:
        item = self.db.scalar(
            select(KnowledgeCollectionItem).where(
                KnowledgeCollectionItem.collection_id == collection_id,
                KnowledgeCollectionItem.document_id == document_id,
            )
        )
        if item is not None:
            self.db.delete(item)
            self.db.flush()

    def serialize(self, c: KnowledgeCollection, *, with_documents: bool = False) -> dict:
        base = {
            "id": str(c.id),
            "slug": c.slug,
            "name": c.name,
            "description": c.description,
            "owner_id": str(c.owner_id) if c.owner_id else None,
            "document_count": len(c.items),
        }
        if with_documents:
            docs = dict(
                self.db.execute(
                    select(KnowledgeDocument.id, KnowledgeDocument.title).where(
                        KnowledgeDocument.id.in_([i.document_id for i in c.items])
                    )
                ).all()
            )
            base["documents"] = [
                {
                    "document_id": str(i.document_id),
                    "title": docs.get(i.document_id),
                    "position": i.position,
                }
                for i in c.items
            ]
        return base
