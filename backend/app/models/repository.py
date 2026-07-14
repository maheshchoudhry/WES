"""Repository Intelligence Engine ORM models (Sprint 12).

Models a scanned software repository as first-class data: files, modules, symbols,
dependencies, relationships, detected architecture layers, a search index, change
history, metrics, issues, and TODOs. This is the software-understanding layer AI
employees consult before generating or reviewing code.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.repository_enums import (
    ArchitectureLayer,
    DependencyType,
    IssueSeverity,
    Language,
    ModuleKind,
    RelationshipType,
    ScanStatus,
    SymbolType,
)
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class Repository(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "repositories"

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    root_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_language: Mapped[str | None] = mapped_column(String(40), nullable=True)
    frameworks: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="registered")
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RepositoryScan(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_scans"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ScanStatus] = mapped_column(
        String(20), nullable=False, default=ScanStatus.QUEUED
    )
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    symbol_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    module_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RepositoryModule(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_modules"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    path: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    kind: Mapped[ModuleKind] = mapped_column(String(20), nullable=False, default=ModuleKind.MODULE)
    language: Mapped[str | None] = mapped_column(String(40), nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class RepositoryFile(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_files"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repository_modules.id", ondelete="SET NULL"), nullable=True
    )
    path: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    extension: Mapped[str | None] = mapped_column(String(40), nullable=True)
    language: Mapped[str] = mapped_column(String(40), nullable=False, default=Language.OTHER)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    symbol_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    layer: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    is_config: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_test: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class RepositorySymbol(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_symbols"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    symbol_type: Mapped[SymbolType] = mapped_column(String(30), nullable=False, index=True)
    line: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent: Mapped[str | None] = mapped_column(String(300), nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    docstring: Mapped[str | None] = mapped_column(Text, nullable=True)


class RepositoryDependency(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_dependencies"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    dependency_type: Mapped[DependencyType] = mapped_column(
        String(20), nullable=False, default=DependencyType.IMPORT
    )
    external: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class RepositoryRelationship(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_relationships"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    relationship_type: Mapped[RelationshipType] = mapped_column(String(20), nullable=False)


class RepositoryArchitecture(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_architecture"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    layer: Mapped[ArchitectureLayer] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    symbol_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class RepositorySearchIndex(UUIDPrimaryKeyMixin, Base):
    """Denormalized search rows (name/kind/file). Semantic-ready seam."""

    __tablename__ = "repository_search_index"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repository_symbols.id", ondelete="CASCADE"), nullable=True
    )
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=True
    )
    term: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RepositoryChangeHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_change_history"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repository_scans.id", ondelete="SET NULL"), nullable=True
    )
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False, default="scanned")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RepositoryMetrics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "repository_metrics"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    module_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    symbol_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    class_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    function_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    route_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dependency_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    test_file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    languages: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    technical_debt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    health_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class RepositoryIssue(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_issues"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repository_files.id", ondelete="SET NULL"), nullable=True
    )
    severity: Mapped[IssueSeverity] = mapped_column(
        String(20), nullable=False, default=IssueSeverity.INFO
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="quality")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RepositoryTodo(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_todos"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repository_files.id", ondelete="SET NULL"), nullable=True
    )
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tag: Mapped[str] = mapped_column(String(20), nullable=False, default="TODO")
    text: Mapped[str] = mapped_column(Text, nullable=False)
