"""Repository + Indexer services (Sprint 12).

RepositoryService owns repository registration. IndexerService runs the scan
pipeline — scan → parse → persist — producing files, modules, symbols,
dependencies, relationships, architecture, a search index, metrics, issues, and
TODOs. Re-scanning is idempotent (previous index rows are replaced).
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.repository_enums import IssueSeverity, ScanStatus, SymbolType
from app.models.repository import (
    Repository,
    RepositoryArchitecture,
    RepositoryChangeHistory,
    RepositoryDependency,
    RepositoryFile,
    RepositoryIssue,
    RepositoryMetrics,
    RepositoryModule,
    RepositoryRelationship,
    RepositoryScan,
    RepositorySearchIndex,
    RepositorySymbol,
    RepositoryTodo,
)
from app.services import repo_parser
from app.services.repo_scanner import scan_tree

_LONG_FILE_LINES = 600


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slugify(text: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "repository"


class RepositoryService:
    def __init__(self, db: Session):
        self.db = db

    def list_repositories(self) -> list[Repository]:
        return list(self.db.scalars(select(Repository).order_by(Repository.name)).all())

    def get(self, repository_id: uuid.UUID) -> Repository:
        r = self.db.get(Repository, repository_id)
        if r is None:
            raise NotFoundError(f"Repository {repository_id} not found")
        return r

    def get_by_slug(self, slug: str) -> Repository | None:
        return self.db.scalar(select(Repository).where(Repository.slug == slug))

    def register(
        self,
        name: str,
        root_path: str,
        *,
        description: str | None = None,
        slug: str | None = None,
        project_id: uuid.UUID | None = None,
    ) -> Repository:
        slug = slug or _slugify(name)
        if self.get_by_slug(slug):
            raise ConflictError(f"Repository '{slug}' already exists")
        repo = Repository(
            slug=slug,
            name=name,
            root_path=os.path.abspath(root_path),
            description=description,
            project_id=project_id,
            status="registered",
        )
        self.db.add(repo)
        self.db.flush()
        return repo

    def serialize(self, r: Repository) -> dict:
        metrics = self.db.scalar(
            select(RepositoryMetrics).where(RepositoryMetrics.repository_id == r.id)
        )
        return {
            "id": str(r.id),
            "slug": r.slug,
            "name": r.name,
            "root_path": r.root_path,
            "description": r.description,
            "primary_language": r.primary_language,
            "frameworks": (r.frameworks.split(",") if r.frameworks else []),
            "status": r.status,
            "last_scanned_at": r.last_scanned_at.isoformat() if r.last_scanned_at else None,
            "metrics": (
                {
                    "file_count": metrics.file_count,
                    "module_count": metrics.module_count,
                    "symbol_count": metrics.symbol_count,
                    "class_count": metrics.class_count,
                    "function_count": metrics.function_count,
                    "route_count": metrics.route_count,
                    "model_count": metrics.model_count,
                    "line_count": metrics.line_count,
                    "dependency_count": metrics.dependency_count,
                    "test_file_count": metrics.test_file_count,
                    "technical_debt": metrics.technical_debt,
                    "health_score": metrics.health_score,
                    "languages": json.loads(metrics.languages) if metrics.languages else {},
                }
                if metrics
                else None
            ),
        }


class IndexerService:
    """The scan pipeline: scan → parse → persist (idempotent re-index)."""

    def __init__(self, db: Session):
        self.db = db

    def _clear(self, repo_id: uuid.UUID) -> None:
        for model in (
            RepositorySearchIndex,
            RepositorySymbol,
            RepositoryDependency,
            RepositoryRelationship,
            RepositoryArchitecture,
            RepositoryIssue,
            RepositoryTodo,
            RepositoryFile,
            RepositoryModule,
            RepositoryMetrics,
        ):
            self.db.execute(delete(model).where(model.repository_id == repo_id))
        self.db.flush()

    def scan(self, repository_id: uuid.UUID, *, max_files: int = 5000) -> RepositoryScan:
        repo = self.db.get(Repository, repository_id)
        if repo is None:
            raise NotFoundError(f"Repository {repository_id} not found")

        scan = RepositoryScan(repository_id=repo.id, status=ScanStatus.RUNNING, started_at=_now())
        self.db.add(scan)
        self.db.flush()
        started = time.monotonic()
        try:
            self._clear(repo.id)
            inventory = scan_tree(repo.root_path, max_files=max_files)
            self._index(repo, scan, inventory)
            scan.status = ScanStatus.COMPLETED
        except Exception as exc:  # pragma: no cover - defensive
            scan.status = ScanStatus.FAILED
            scan.error = str(exc)[:500]
            self.db.flush()
            return scan
        scan.duration_ms = int((time.monotonic() - started) * 1000)
        scan.completed_at = _now()
        self.db.flush()
        return scan

    def _index(self, repo: Repository, scan: RepositoryScan, inventory: list) -> None:
        # 1. Modules (unique directories).
        module_rows: dict[str, RepositoryModule] = {}
        for f in inventory:
            if f.module_path not in module_rows:
                m = RepositoryModule(
                    repository_id=repo.id,
                    path=f.module_path,
                    name=os.path.basename(f.module_path) or repo.name,
                    kind=(
                        "package"
                        if any(
                            x.name == "__init__.py" and x.module_path == f.module_path
                            for x in inventory
                        )
                        else "directory"
                    ),
                )
                self.db.add(m)
                module_rows[f.module_path] = m
        self.db.flush()

        # 2. Files + parse.
        lang_counts: dict[str, int] = {}
        totals = {
            "symbols": 0,
            "classes": 0,
            "functions": 0,
            "routes": 0,
            "models": 0,
            "lines": 0,
            "deps": 0,
            "tests": 0,
            "todos": 0,
        }
        frameworks: set[str] = set()
        for f in inventory:
            lang_counts[f.language.value] = lang_counts.get(f.language.value, 0) + 1
            if f.is_test:
                totals["tests"] += 1
            file_row = RepositoryFile(
                repository_id=repo.id,
                module_id=module_rows[f.module_path].id,
                path=f.path,
                name=f.name,
                extension=f.extension or None,
                language=f.language.value,
                size_bytes=f.size_bytes,
                layer=f.layer.value,
                is_config=f.is_config,
                is_generated=f.is_generated,
                is_test=f.is_test,
            )
            self.db.add(file_row)
            self.db.flush()
            module_rows[f.module_path].file_count += 1

            # File search row.
            self.db.add(
                RepositorySearchIndex(
                    repository_id=repo.id,
                    file_id=file_row.id,
                    term=f.name,
                    kind="file",
                    file_path=f.path,
                )
            )

            if not f.parseable:
                continue
            try:
                with open(f.abs_path, encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
            except OSError:  # pragma: no cover
                continue
            result = repo_parser.parse(f.name, content, f.language)
            file_row.line_count = result.line_count
            file_row.symbol_count = len(result.symbols)
            totals["lines"] += result.line_count

            for sym in result.symbols:
                srow = RepositorySymbol(
                    repository_id=repo.id,
                    file_id=file_row.id,
                    name=sym.name,
                    symbol_type=sym.symbol_type.value,
                    line=sym.line,
                    end_line=sym.end_line,
                    parent=sym.parent,
                    signature=sym.signature,
                    docstring=sym.docstring,
                )
                self.db.add(srow)
                self.db.flush()
                totals["symbols"] += 1
                if sym.symbol_type in (
                    SymbolType.CLASS,
                    SymbolType.MODEL,
                    SymbolType.SCHEMA,
                    SymbolType.ENUM,
                ):
                    totals["classes"] += 1
                if sym.symbol_type in (SymbolType.FUNCTION, SymbolType.METHOD):
                    totals["functions"] += 1
                if sym.symbol_type == SymbolType.ROUTE:
                    totals["routes"] += 1
                if sym.symbol_type == SymbolType.MODEL:
                    totals["models"] += 1
                self.db.add(
                    RepositorySearchIndex(
                        repository_id=repo.id,
                        symbol_id=srow.id,
                        file_id=file_row.id,
                        term=sym.name,
                        kind=sym.symbol_type.value,
                        file_path=f.path,
                        line=sym.line,
                    )
                )
            for imp in result.imports:
                self.db.add(
                    RepositoryDependency(
                        repository_id=repo.id,
                        source=f.path,
                        target=imp.target,
                        dependency_type="package" if imp.external else "import",
                        external=imp.external,
                    )
                )
                totals["deps"] += 1
                if imp.external and imp.target in {
                    "fastapi",
                    "react",
                    "sqlalchemy",
                    "pydantic",
                    "alembic",
                    "vite",
                }:
                    frameworks.add(imp.target)
            for src, tgt, rtype in result.relationships:
                self.db.add(
                    RepositoryRelationship(
                        repository_id=repo.id, source=src, target=tgt, relationship_type=rtype
                    )
                )
            for todo in result.todos:
                self.db.add(
                    RepositoryTodo(
                        repository_id=repo.id,
                        file_id=file_row.id,
                        file_path=f.path,
                        line=todo.line,
                        tag=todo.tag,
                        text=todo.text,
                    )
                )
                totals["todos"] += 1
            # Issue heuristic: overly long files are technical debt.
            if result.line_count > _LONG_FILE_LINES:
                self.db.add(
                    RepositoryIssue(
                        repository_id=repo.id,
                        file_id=file_row.id,
                        severity=IssueSeverity.LOW,
                        category="maintainability",
                        message=f"Large file ({result.line_count} lines) — consider splitting",
                        file_path=f.path,
                        line=1,
                    )
                )
        self.db.flush()

        # 3. Architecture layers (aggregate files by layer).
        layer_agg = self.db.execute(
            select(
                RepositoryFile.layer,
                func.count(RepositoryFile.id),
                func.coalesce(func.sum(RepositoryFile.symbol_count), 0),
            )
            .where(RepositoryFile.repository_id == repo.id)
            .group_by(RepositoryFile.layer)
        ).all()
        for layer, count, symbols in layer_agg:
            if not layer:
                continue
            self.db.add(
                RepositoryArchitecture(
                    repository_id=repo.id,
                    layer=layer,
                    name=layer.replace("_", " ").title(),
                    file_count=count,
                    symbol_count=int(symbols or 0),
                    description=f"{count} files in the {layer} layer",
                )
            )

        # 4. Metrics + health.
        debt = totals["todos"] + self.db.scalar(
            select(func.count(RepositoryIssue.id)).where(RepositoryIssue.repository_id == repo.id)
        )
        source_files = sum(1 for f in inventory if f.parseable and not f.is_test)
        documented = self.db.scalar(
            select(func.count(RepositorySymbol.id)).where(
                RepositorySymbol.repository_id == repo.id,
                RepositorySymbol.docstring.is_not(None),
            )
        )
        doc_ratio = (documented / totals["symbols"]) if totals["symbols"] else 0.0
        test_ratio = (totals["tests"] / source_files) if source_files else 0.0
        health = round(
            min(100.0, 40 + doc_ratio * 40 + min(test_ratio, 1.0) * 20 - min(debt, 20)), 1
        )

        self.db.add(
            RepositoryMetrics(
                repository_id=repo.id,
                file_count=len(inventory),
                module_count=len(module_rows),
                symbol_count=totals["symbols"],
                class_count=totals["classes"],
                function_count=totals["functions"],
                route_count=totals["routes"],
                model_count=totals["models"],
                line_count=totals["lines"],
                dependency_count=totals["deps"],
                test_file_count=totals["tests"],
                languages=json.dumps(lang_counts),
                technical_debt=debt,
                health_score=max(0.0, health),
            )
        )

        # 5. Repository summary + scan counts + change history.
        primary = max(lang_counts, key=lang_counts.get) if lang_counts else None
        repo.primary_language = primary
        repo.frameworks = ",".join(sorted(frameworks)) if frameworks else None
        repo.status = "indexed"
        repo.last_scanned_at = _now()
        scan.file_count = len(inventory)
        scan.symbol_count = totals["symbols"]
        scan.module_count = len(module_rows)
        scan.summary = (
            f"{len(inventory)} files, {totals['symbols']} symbols, "
            f"{totals['routes']} routes, {totals['models']} models"
        )
        self.db.add(
            RepositoryChangeHistory(
                repository_id=repo.id,
                scan_id=scan.id,
                change_type="scanned",
                detail=scan.summary,
            )
        )
        self.db.flush()
