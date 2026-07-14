"""repository intelligence engine schema

Creates repositories, repository_scans, repository_modules, repository_files,
repository_symbols, repository_dependencies, repository_relationships,
repository_architecture, repository_search_index, repository_change_history,
repository_metrics, repository_issues, and repository_todos.

Revision ID: 0009_repository_intelligence
Revises: 0008_live_provider_platform
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision: str = "0009_repository_intelligence"
down_revision: Union[str, None] = "0008_live_provider_platform"
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
        "repositories",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("root_path", sa.String(length=1000), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("primary_language", sa.String(length=40), nullable=True),
        sa.Column("frameworks", sa.Text(), nullable=True),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="registered"),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_repositories_slug"),
    )
    op.create_index("ix_repositories_slug", "repositories", ["slug"])

    op.create_table(
        "repository_scans",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("symbol_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("module_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repository_scans_repository_id", "repository_scans", ["repository_id"])

    op.create_table(
        "repository_modules",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("path", sa.String(length=1000), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="module"),
        sa.Column("language", sa.String(length=40), nullable=True),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repository_modules_repository_id", "repository_modules", ["repository_id"])
    op.create_index("ix_repository_modules_path", "repository_modules", ["path"])

    op.create_table(
        "repository_files",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("module_id", GUID(), nullable=True),
        sa.Column("path", sa.String(length=1000), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("extension", sa.String(length=40), nullable=True),
        sa.Column("language", sa.String(length=40), nullable=False, server_default="other"),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("line_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("symbol_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("layer", sa.String(length=30), nullable=True),
        sa.Column("is_config", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_test", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["repository_modules.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repository_files_repository_id", "repository_files", ["repository_id"])
    op.create_index("ix_repository_files_path", "repository_files", ["path"])
    op.create_index("ix_repository_files_layer", "repository_files", ["layer"])

    op.create_table(
        "repository_symbols",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("file_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("symbol_type", sa.String(length=30), nullable=False),
        sa.Column("line", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("parent", sa.String(length=300), nullable=True),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column("docstring", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["repository_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repository_symbols_repository_id", "repository_symbols", ["repository_id"])
    op.create_index("ix_repository_symbols_file_id", "repository_symbols", ["file_id"])
    op.create_index("ix_repository_symbols_name", "repository_symbols", ["name"])
    op.create_index("ix_repository_symbols_symbol_type", "repository_symbols", ["symbol_type"])

    op.create_table(
        "repository_dependencies",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("source", sa.String(length=1000), nullable=False),
        sa.Column("target", sa.String(length=1000), nullable=False),
        sa.Column("dependency_type", sa.String(length=20), nullable=False, server_default="import"),
        sa.Column("external", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_repository_dependencies_repository_id", "repository_dependencies", ["repository_id"]
    )
    op.create_index("ix_repository_dependencies_source", "repository_dependencies", ["source"])
    op.create_index("ix_repository_dependencies_target", "repository_dependencies", ["target"])

    op.create_table(
        "repository_relationships",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("source", sa.String(length=300), nullable=False),
        sa.Column("target", sa.String(length=300), nullable=False),
        sa.Column("relationship_type", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_repository_relationships_repository_id", "repository_relationships", ["repository_id"]
    )
    op.create_index("ix_repository_relationships_source", "repository_relationships", ["source"])
    op.create_index("ix_repository_relationships_target", "repository_relationships", ["target"])

    op.create_table(
        "repository_architecture",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("layer", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("symbol_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_repository_architecture_repository_id", "repository_architecture", ["repository_id"]
    )
    op.create_index("ix_repository_architecture_layer", "repository_architecture", ["layer"])

    op.create_table(
        "repository_search_index",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("symbol_id", GUID(), nullable=True),
        sa.Column("file_id", GUID(), nullable=True),
        sa.Column("term", sa.String(length=300), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["symbol_id"], ["repository_symbols.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["repository_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_repository_search_index_repository_id", "repository_search_index", ["repository_id"]
    )
    op.create_index("ix_repository_search_index_term", "repository_search_index", ["term"])
    op.create_index("ix_repository_search_index_kind", "repository_search_index", ["kind"])

    op.create_table(
        "repository_change_history",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("scan_id", GUID(), nullable=True),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("change_type", sa.String(length=20), nullable=False, server_default="scanned"),
        sa.Column("detail", sa.Text(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["repository_scans.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_repository_change_history_repository_id",
        "repository_change_history",
        ["repository_id"],
    )

    op.create_table(
        "repository_metrics",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("module_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("symbol_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("class_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("function_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("route_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("model_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("line_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("dependency_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("test_file_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("languages", sa.Text(), nullable=True),
        sa.Column("technical_debt", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("health_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        *_ts(),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_repository_metrics_repository_id", "repository_metrics", ["repository_id"]
    )

    op.create_table(
        "repository_issues",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("file_id", GUID(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="quality"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
        _created(),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["repository_files.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repository_issues_repository_id", "repository_issues", ["repository_id"])

    op.create_table(
        "repository_todos",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("file_id", GUID(), nullable=True),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("line", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("tag", sa.String(length=20), nullable=False, server_default="TODO"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["repository_files.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repository_todos_repository_id", "repository_todos", ["repository_id"])


def downgrade() -> None:
    for tbl in (
        "repository_todos",
        "repository_issues",
        "repository_metrics",
        "repository_change_history",
        "repository_search_index",
        "repository_architecture",
        "repository_relationships",
        "repository_dependencies",
        "repository_symbols",
        "repository_files",
        "repository_modules",
        "repository_scans",
        "repositories",
    ):
        op.drop_table(tbl)
