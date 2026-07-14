"""organizational knowledge engine schema

Creates the knowledge layer: categories, tags, documents (+ document/tag join),
relationships, versions, reviews, sources, references, embeddings placeholder,
access log, bookmarks, collections (+ collection items), and architecture
decision records.

Revision ID: 0007_organizational_knowledge_engine
Revises: 0006_ai_orchestration_engine
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0007_organizational_knowledge_engine"
down_revision: Union[str, None] = "0006_ai_orchestration_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return (
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def _created():
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "knowledge_categories",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", GUID(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        *_ts(),
        sa.ForeignKeyConstraint(["parent_id"], ["knowledge_categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_knowledge_categories_code"),
    )
    op.create_index("ix_knowledge_categories_code", "knowledge_categories", ["code"])

    op.create_table(
        "knowledge_tags",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        *_ts(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_knowledge_tags_slug"),
    )
    op.create_index("ix_knowledge_tags_slug", "knowledge_tags", ["slug"])

    op.create_table(
        "knowledge_documents",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("doc_type", sa.String(length=40), nullable=False),
        sa.Column("category_id", GUID(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("author_id", GUID(), nullable=True),
        sa.Column("approver_id", GUID(), nullable=True),
        sa.Column("owner_ai_employee_id", GUID(), nullable=True),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        *_ts(),
        sa.ForeignKeyConstraint(["category_id"], ["knowledge_categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["author_id"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approver_id"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["owner_ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_knowledge_documents_code"),
    )
    op.create_index("ix_knowledge_documents_code", "knowledge_documents", ["code"])
    op.create_index("ix_knowledge_documents_slug", "knowledge_documents", ["slug"])
    op.create_index("ix_knowledge_documents_doc_type", "knowledge_documents", ["doc_type"])
    op.create_index("ix_knowledge_documents_category_id", "knowledge_documents", ["category_id"])
    op.create_index("ix_knowledge_documents_status", "knowledge_documents", ["status"])

    op.create_table(
        "knowledge_document_tags",
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("tag_id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["knowledge_tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id", "tag_id"),
    )

    op.create_table(
        "knowledge_relationships",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("source_document_id", GUID(), nullable=False),
        sa.Column("target_document_id", GUID(), nullable=False),
        sa.Column("relationship_type", sa.String(length=30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_relationships_source_document_id",
        "knowledge_relationships",
        ["source_document_id"],
    )
    op.create_index(
        "ix_knowledge_relationships_target_document_id",
        "knowledge_relationships",
        ["target_document_id"],
    )

    op.create_table(
        "knowledge_versions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("author_id", GUID(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["author_id"], ["employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_versions_document_id", "knowledge_versions", ["document_id"])

    op.create_table(
        "knowledge_reviews",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("reviewer_id", GUID(), nullable=True),
        sa.Column("reviewer_name", sa.String(length=200), nullable=True),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["reviewer_id"], ["employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_reviews_document_id", "knowledge_reviews", ["document_id"])

    op.create_table(
        "knowledge_sources",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False, server_default="internal"),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_sources_document_id", "knowledge_sources", ["document_id"])

    op.create_table(
        "knowledge_references",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("entity_id", GUID(), nullable=True),
        sa.Column("label", sa.String(length=300), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_references_document_id", "knowledge_references", ["document_id"])
    op.create_index("ix_knowledge_references_entity_type", "knowledge_references", ["entity_type"])
    op.create_index("ix_knowledge_references_entity_id", "knowledge_references", ["entity_id"])

    op.create_table(
        "knowledge_embeddings_placeholder",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("vector_dim", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("note", sa.Text(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_embeddings_placeholder_document_id",
        "knowledge_embeddings_placeholder",
        ["document_id"],
    )

    op.create_table(
        "knowledge_access_log",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("actor", sa.String(length=200), nullable=True),
        sa.Column("ai_employee_id", GUID(), nullable=True),
        sa.Column("action", sa.String(length=20), nullable=False, server_default="view"),
        sa.Column("context", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["ai_employee_id"], ["ai_employees.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_access_log_document_id", "knowledge_access_log", ["document_id"])

    op.create_table(
        "knowledge_bookmarks",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_bookmarks_document_id", "knowledge_bookmarks", ["document_id"])
    op.create_index("ix_knowledge_bookmarks_user_id", "knowledge_bookmarks", ["user_id"])

    op.create_table(
        "knowledge_collections",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", GUID(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["owner_id"], ["employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_knowledge_collections_slug"),
    )
    op.create_index("ix_knowledge_collections_slug", "knowledge_collections", ["slug"])

    op.create_table(
        "knowledge_collection_items",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("collection_id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["knowledge_collections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_collection_items_collection_id",
        "knowledge_collection_items",
        ["collection_id"],
    )
    op.create_index(
        "ix_knowledge_collection_items_document_id",
        "knowledge_collection_items",
        ["document_id"],
    )

    op.create_table(
        "architecture_decision_records",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="proposed"),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("consequences", sa.Text(), nullable=True),
        sa.Column("document_id", GUID(), nullable=True),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("decided_by_id", GUID(), nullable=True),
        sa.Column("supersedes_adr_id", GUID(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["decided_by_id"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["supersedes_adr_id"], ["architecture_decision_records.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_architecture_decision_records_code"),
    )
    op.create_index(
        "ix_architecture_decision_records_code", "architecture_decision_records", ["code"]
    )
    op.create_index(
        "ix_architecture_decision_records_status", "architecture_decision_records", ["status"]
    )


def downgrade() -> None:
    for tbl in (
        "architecture_decision_records",
        "knowledge_collection_items",
        "knowledge_collections",
        "knowledge_bookmarks",
        "knowledge_access_log",
        "knowledge_embeddings_placeholder",
        "knowledge_references",
        "knowledge_sources",
        "knowledge_reviews",
        "knowledge_versions",
        "knowledge_relationships",
        "knowledge_document_tags",
        "knowledge_documents",
        "knowledge_tags",
        "knowledge_categories",
    ):
        op.drop_table(tbl)
