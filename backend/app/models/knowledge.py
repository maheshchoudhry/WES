"""Organizational Knowledge Engine ORM models (Sprint 10).

The knowledge layer is the single source of truth for WES. Documents carry a
type, category, status, and full text; a knowledge graph links documents to each
other and to organizational entities (projects, employees, tasks, SOPs, ADRs,
standards). Versioning, reviews/approvals, sources, bookmarks, collections, an
access log, and an embeddings placeholder (for future vector search) complete
the model.

The embeddings table is a *placeholder*: it records that a document is ready for
vectorization and which model would be used, but stores no vectors. Semantic
search can be added later without changing this data model or the public APIs.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.knowledge_enums import (
    ADRStatus,
    DocumentType,
    KnowledgeStatus,
    ReferenceEntityType,
    RelationshipType,
    ReviewDecision,
    SourceType,
)
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin

# Many-to-many: documents <-> tags.
knowledge_document_tags = Table(
    "knowledge_document_tags",
    Base.metadata,
    Column(
        "document_id",
        GUID(),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        GUID(),
        ForeignKey("knowledge_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class KnowledgeCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_categories"

    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("knowledge_categories.id", ondelete="SET NULL"), nullable=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class KnowledgeTag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_tags"

    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(String(40), nullable=False, index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("knowledge_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[KnowledgeStatus] = mapped_column(
        String(20), nullable=False, default=KnowledgeStatus.DRAFT, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    owner_ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    category: Mapped["KnowledgeCategory | None"] = relationship()
    tags: Mapped[list["KnowledgeTag"]] = relationship(secondary=knowledge_document_tags)


class KnowledgeRelationship(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_relationships"

    source_document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(String(30), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class KnowledgeVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[KnowledgeStatus] = mapped_column(String(20), nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class KnowledgeReview(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_reviews"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    reviewer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    decision: Mapped[ReviewDecision] = mapped_column(String(30), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class KnowledgeSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_sources"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[SourceType] = mapped_column(
        String(20), nullable=False, default=SourceType.INTERNAL
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class KnowledgeReference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A link from a document to an organizational entity (knowledge graph edge)."""

    __tablename__ = "knowledge_references"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[ReferenceEntityType] = mapped_column(String(30), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    label: Mapped[str | None] = mapped_column(String(300), nullable=True)


class KnowledgeEmbeddingPlaceholder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Marks a document as ready for vectorization; stores no vectors.

    Future semantic search populates real embeddings against this row without any
    change to the public data model or APIs.
    """

    __tablename__ = "knowledge_embeddings_placeholder"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    vector_dim: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class KnowledgeAccessLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_access_log"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False, default="view")
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class KnowledgeBookmark(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_bookmarks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# Many-to-many: collections <-> documents (ordered).
class KnowledgeCollectionItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_collection_items"

    collection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("knowledge_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class KnowledgeCollection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_collections"

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )

    items: Mapped[list["KnowledgeCollectionItem"]] = relationship(
        cascade="all, delete-orphan", order_by="KnowledgeCollectionItem.position"
    )


class ArchitectureDecisionRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "architecture_decision_records"

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[ADRStatus] = mapped_column(
        String(20), nullable=False, default=ADRStatus.PROPOSED, index=True
    )
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    consequences: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    decided_by_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    supersedes_adr_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("architecture_decision_records.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
