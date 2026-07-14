"""Repository analysis services (Sprint 12).

Symbol, Dependency, Search, Impact, Architecture, and Documentation services over
the indexed repository, plus the founder/AI dashboards and the AI retrieval
service. Search is backend-agnostic (LIKE today) with a semantic-ready seam, and
retrieval assembles the repository context an AI employee consumes before writing
or reviewing code.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.repository_enums import SymbolType
from app.models.knowledge import KnowledgeReference
from app.models.repository import (
    Repository,
    RepositoryArchitecture,
    RepositoryDependency,
    RepositoryFile,
    RepositoryIssue,
    RepositoryMetrics,
    RepositoryModule,
    RepositoryRelationship,
    RepositorySearchIndex,
    RepositorySymbol,
    RepositoryTodo,
)


def _sym_dict(s: RepositorySymbol, file_path: str | None = None) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "symbol_type": s.symbol_type.value if hasattr(s.symbol_type, "value") else s.symbol_type,
        "line": s.line,
        "end_line": s.end_line,
        "parent": s.parent,
        "signature": s.signature,
        "docstring": s.docstring,
        "file_id": str(s.file_id),
        "file_path": file_path,
    }


class SymbolService:
    def __init__(self, db: Session):
        self.db = db

    def _paths(self, repo_id) -> dict:
        return {
            f.id: f.path
            for f in self.db.scalars(
                select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
            ).all()
        }

    def list_symbols(
        self, repo_id: uuid.UUID, *, symbol_type: str | None = None, limit: int = 200
    ) -> list[dict]:
        stmt = select(RepositorySymbol).where(RepositorySymbol.repository_id == repo_id)
        if symbol_type:
            stmt = stmt.where(RepositorySymbol.symbol_type == symbol_type)
        stmt = stmt.order_by(RepositorySymbol.name).limit(limit)
        paths = self._paths(repo_id)
        return [_sym_dict(s, paths.get(s.file_id)) for s in self.db.scalars(stmt).all()]

    def for_file(self, file_id: uuid.UUID) -> list[dict]:
        rows = self.db.scalars(
            select(RepositorySymbol)
            .where(RepositorySymbol.file_id == file_id)
            .order_by(RepositorySymbol.line)
        ).all()
        return [_sym_dict(s) for s in rows]

    def references(self, repo_id: uuid.UUID, name: str) -> list[dict]:
        """Cross-reference: everywhere a symbol name is defined or referenced."""
        defs = self.db.scalars(
            select(RepositorySymbol).where(
                RepositorySymbol.repository_id == repo_id, RepositorySymbol.name == name
            )
        ).all()
        rels = self.db.scalars(
            select(RepositoryRelationship).where(
                RepositoryRelationship.repository_id == repo_id,
                or_(
                    RepositoryRelationship.source == name,
                    RepositoryRelationship.target == name,
                ),
            )
        ).all()
        paths = self._paths(repo_id)
        return {
            "definitions": [_sym_dict(s, paths.get(s.file_id)) for s in defs],
            "relationships": [
                {
                    "source": r.source,
                    "target": r.target,
                    "type": (
                        r.relationship_type.value
                        if hasattr(r.relationship_type, "value")
                        else r.relationship_type
                    ),
                }
                for r in rels
            ],
        }


class DependencyService:
    def __init__(self, db: Session):
        self.db = db

    def import_graph(
        self, repo_id: uuid.UUID, *, internal_only: bool = True, limit: int = 500
    ) -> dict:
        stmt = select(RepositoryDependency).where(RepositoryDependency.repository_id == repo_id)
        if internal_only:
            stmt = stmt.where(RepositoryDependency.external.is_(False))
        deps = list(self.db.scalars(stmt.limit(limit)).all())
        files = {
            f.path: f
            for f in self.db.scalars(
                select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
            ).all()
        }
        nodes = {}
        edges = []
        for d in deps:
            nodes.setdefault(
                d.source,
                {
                    "id": d.source,
                    "layer": files.get(d.source).layer if files.get(d.source) else None,
                },
            )
            nodes.setdefault(d.target, {"id": d.target, "layer": None})
            edges.append({"source": d.source, "target": d.target, "external": d.external})
        return {"nodes": list(nodes.values()), "edges": edges}

    def module_graph(self, repo_id: uuid.UUID) -> dict:
        """Aggregate the import graph to module (directory) level."""
        files = {
            f.path: f.module_id
            for f in self.db.scalars(
                select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
            ).all()
        }
        modules = {
            m.id: m
            for m in self.db.scalars(
                select(RepositoryModule).where(RepositoryModule.repository_id == repo_id)
            ).all()
        }
        deps = self.db.scalars(
            select(RepositoryDependency).where(
                RepositoryDependency.repository_id == repo_id,
                RepositoryDependency.external.is_(False),
            )
        ).all()
        edge_set = set()
        for d in deps:
            src_mod = files.get(d.source)
            # target is a module path like "app.services.x"; map by suffix match.
            tgt_mod = None
            tgt = d.target.replace(".", "/")
            for path, mid in files.items():
                if path.replace("\\", "/").startswith(tgt) or tgt in path.replace("\\", "/"):
                    tgt_mod = mid
                    break
            if src_mod and tgt_mod and src_mod != tgt_mod:
                edge_set.add((src_mod, tgt_mod))
        nodes = [
            {"id": str(m.id), "name": m.path, "file_count": m.file_count} for m in modules.values()
        ]
        edges = [{"source": str(s), "target": str(t)} for s, t in edge_set]
        return {"nodes": nodes, "edges": edges}

    def external_dependencies(self, repo_id: uuid.UUID) -> list[dict]:
        rows = self.db.execute(
            select(RepositoryDependency.target, func.count(RepositoryDependency.id))
            .where(
                RepositoryDependency.repository_id == repo_id,
                RepositoryDependency.external.is_(True),
            )
            .group_by(RepositoryDependency.target)
            .order_by(func.count(RepositoryDependency.id).desc())
        ).all()
        return [{"package": pkg, "usages": count} for pkg, count in rows]


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(
        self, repo_id: uuid.UUID, query: str, *, kind: str | None = None, limit: int = 50
    ) -> list[dict]:
        """Unified repository search (file/class/function/symbol/route/model).

        LIKE-based today; the row shape and signature are stable so a semantic
        backend can replace the matching without changing callers.
        """
        stmt = select(RepositorySearchIndex).where(RepositorySearchIndex.repository_id == repo_id)
        if query:
            stmt = stmt.where(func.lower(RepositorySearchIndex.term).like(f"%{query.lower()}%"))
        if kind:
            stmt = stmt.where(RepositorySearchIndex.kind == kind)
        stmt = stmt.order_by(RepositorySearchIndex.term).limit(limit)
        return [
            {
                "term": r.term,
                "kind": r.kind,
                "file_path": r.file_path,
                "line": r.line,
                "symbol_id": str(r.symbol_id) if r.symbol_id else None,
                "file_id": str(r.file_id) if r.file_id else None,
            }
            for r in self.db.scalars(stmt).all()
        ]


class ArchitectureService:
    def __init__(self, db: Session):
        self.db = db

    def layers(self, repo_id: uuid.UUID) -> list[dict]:
        rows = self.db.scalars(
            select(RepositoryArchitecture)
            .where(RepositoryArchitecture.repository_id == repo_id)
            .order_by(RepositoryArchitecture.file_count.desc())
        ).all()
        return [
            {
                "layer": r.layer.value if hasattr(r.layer, "value") else r.layer,
                "name": r.name,
                "file_count": r.file_count,
                "symbol_count": r.symbol_count,
                "description": r.description,
            }
            for r in rows
        ]

    def modules(self, repo_id: uuid.UUID) -> list[dict]:
        rows = self.db.scalars(
            select(RepositoryModule)
            .where(RepositoryModule.repository_id == repo_id)
            .order_by(RepositoryModule.file_count.desc())
        ).all()
        return [
            {
                "id": str(m.id),
                "path": m.path,
                "name": m.name,
                "kind": m.kind.value if hasattr(m.kind, "value") else m.kind,
                "file_count": m.file_count,
            }
            for m in rows
        ]


class ImpactAnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def analyze(self, repo_id: uuid.UUID, file_path: str) -> dict:
        """Given a file: its dependencies, dependents, related tests/APIs/docs."""
        repo = self.db.get(Repository, repo_id)
        if repo is None:
            raise NotFoundError(f"Repository {repo_id} not found")
        # Dependencies: what this file imports (internal).
        deps = self.db.scalars(
            select(RepositoryDependency).where(
                RepositoryDependency.repository_id == repo_id,
                RepositoryDependency.source == file_path,
                RepositoryDependency.external.is_(False),
            )
        ).all()
        # Dependents: who imports this file's module.
        module_key = file_path.replace("\\", "/").rsplit(".", 1)[0]
        dependents = self.db.scalars(
            select(RepositoryDependency).where(
                RepositoryDependency.repository_id == repo_id,
                RepositoryDependency.external.is_(False),
                or_(
                    RepositoryDependency.target.like(f"%{module_key.replace('/', '.')}%"),
                    RepositoryDependency.target.like(f"%{module_key.rsplit('/', 1)[-1]}%"),
                ),
            )
        ).all()
        dependent_files = sorted({d.source for d in dependents if d.source != file_path})
        # Related tests: test files that reference this file's stem.
        stem = file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        tests = self.db.scalars(
            select(RepositoryFile).where(
                RepositoryFile.repository_id == repo_id,
                RepositoryFile.is_test.is_(True),
                RepositoryFile.name.like(f"%{stem}%"),
            )
        ).all()
        # Related APIs: routes defined in this file.
        this_file = self.db.scalar(
            select(RepositoryFile).where(
                RepositoryFile.repository_id == repo_id, RepositoryFile.path == file_path
            )
        )
        routes = []
        if this_file is not None:
            routes = self.db.scalars(
                select(RepositorySymbol).where(
                    RepositorySymbol.file_id == this_file.id,
                    RepositorySymbol.symbol_type == SymbolType.ROUTE,
                )
            ).all()
        # Related documentation: Knowledge references pointing at this repository.
        docs = self.db.scalars(
            select(KnowledgeReference).where(KnowledgeReference.entity_type == "repository")
        ).all()
        return {
            "file_path": file_path,
            "dependencies": [d.target for d in deps],
            "dependents": dependent_files,
            "potential_breakages": dependent_files,
            "related_tests": [t.path for t in tests],
            "related_apis": [
                {"name": r.name, "signature": r.signature, "line": r.line} for r in routes
            ],
            "related_documentation": [d.label for d in docs if d.label],
        }


class DocumentationService:
    """Connects source files to the Knowledge Engine and markdown docs."""

    def __init__(self, db: Session):
        self.db = db

    def links(self, repo_id: uuid.UUID) -> dict:
        md_files = self.db.scalars(
            select(RepositoryFile).where(
                RepositoryFile.repository_id == repo_id, RepositoryFile.language == "markdown"
            )
        ).all()
        knowledge_refs = self.db.scalars(
            select(KnowledgeReference).where(KnowledgeReference.entity_type == "repository")
        ).all()
        return {
            "markdown_docs": [{"path": f.path, "name": f.name} for f in md_files],
            "knowledge_references": [
                {"document_id": str(r.document_id), "label": r.label} for r in knowledge_refs
            ],
        }


class RepositoryRetrievalService:
    """Repository context assembled for an AI employee before code work."""

    def __init__(self, db: Session):
        self.db = db
        self.search = SearchService(db)

    def retrieve_for(self, keywords: str | None = None, *, limit: int = 6) -> dict:
        repo = self.db.scalar(select(Repository).order_by(Repository.last_scanned_at.desc()))
        if repo is None:
            return {
                "repository": None,
                "relevant_files": [],
                "relevant_symbols": [],
                "architecture": [],
            }
        hits = self.search.search(repo.id, keywords, limit=limit) if keywords else []
        arch = ArchitectureService(self.db).layers(repo.id)
        metrics = self.db.scalar(
            select(RepositoryMetrics).where(RepositoryMetrics.repository_id == repo.id)
        )
        return {
            "repository": {
                "id": str(repo.id),
                "name": repo.name,
                "primary_language": repo.primary_language,
                "health_score": metrics.health_score if metrics else None,
            },
            "relevant_files": [h for h in hits if h["kind"] == "file"][:limit],
            "relevant_symbols": [h for h in hits if h["kind"] != "file"][:limit],
            "architecture": [{"layer": a["layer"], "file_count": a["file_count"]} for a in arch],
        }


class RepositoryDashboard:
    def __init__(self, db: Session):
        self.db = db

    def founder(self, repo_id: uuid.UUID) -> dict:
        from app.services.repository_service import RepositoryService

        repo = self.db.get(Repository, repo_id)
        if repo is None:
            raise NotFoundError(f"Repository {repo_id} not found")
        data = RepositoryService(self.db).serialize(repo)
        data["architecture"] = ArchitectureService(self.db).layers(repo_id)
        data["external_dependencies"] = DependencyService(self.db).external_dependencies(repo_id)[
            :10
        ]
        data["issues"] = [
            {
                "severity": i.severity.value if hasattr(i.severity, "value") else i.severity,
                "category": i.category,
                "message": i.message,
                "file_path": i.file_path,
            }
            for i in self.db.scalars(
                select(RepositoryIssue).where(RepositoryIssue.repository_id == repo_id).limit(20)
            ).all()
        ]
        data["todo_count"] = self.db.scalar(
            select(func.count(RepositoryTodo.id)).where(RepositoryTodo.repository_id == repo_id)
        )
        return data

    def ai(self, keywords: str | None = None) -> dict:
        return RepositoryRetrievalService(self.db).retrieve_for(keywords)
