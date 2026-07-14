"""Repository scanner (Sprint 12).

Walks a real filesystem tree and classifies every file: language, module,
architecture layer, and whether it is config / generated / test / ignored. It
does not parse code (that is the parser's job) — it produces the file inventory
the indexer then parses and stores.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.domain.repository_enums import ArchitectureLayer, Language
from app.services.repo_parser import detect_language

# Directories never scanned (VCS, dependencies, build output, caches).
IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "coverage",
    ".idea",
    ".vscode",
    "htmlcov",
}
# Generated / vendored files (recorded but flagged, not treated as source).
GENERATED_SUFFIXES = (".min.js", ".map", ".lock", ".pyc")
GENERATED_NAMES = {"package-lock.json", "yarn.lock", "poetry.lock", "pnpm-lock.yaml"}
CONFIG_NAMES = {
    "package.json",
    "tsconfig.json",
    "vite.config.ts",
    "pyproject.toml",
    "alembic.ini",
    "requirements.txt",
    "docker-compose.yml",
    ".env.example",
    "eslintrc",
    ".prettierrc",
}
CONFIG_LANGS = {Language.YAML, Language.REQUIREMENTS, Language.DOCKERFILE}
# Only these are read + parsed; everything else is inventoried only.
PARSEABLE = {
    Language.PYTHON,
    Language.TYPESCRIPT,
    Language.JAVASCRIPT,
    Language.JSON,
    Language.SQL,
    Language.DOCKERFILE,
    Language.REQUIREMENTS,
    Language.MARKDOWN,
    Language.YAML,
}


@dataclass
class ScannedFile:
    path: str  # relative to repo root
    abs_path: str
    name: str
    extension: str
    language: Language
    size_bytes: int
    module_path: str  # relative directory
    layer: ArchitectureLayer
    is_config: bool
    is_generated: bool
    is_test: bool
    parseable: bool


def _is_test(rel_path: str, name: str) -> bool:
    lower = rel_path.lower()
    return (
        "/tests/" in f"/{lower}"
        or "/__tests__/" in f"/{lower}"
        or name.startswith("test_")
        or name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".test.js"))
    )


def detect_layer(
    rel_path: str, language: Language, is_test: bool, is_config: bool
) -> ArchitectureLayer:
    p = f"/{rel_path.lower()}/"
    if is_test:
        return ArchitectureLayer.TEST
    if "/alembic/" in p or "/migrations/" in p:
        return ArchitectureLayer.MIGRATION
    if "/docs/" in p or language == Language.MARKDOWN:
        return ArchitectureLayer.DOCUMENTATION
    if "/frontend/" in p:
        # Refine the frontend by sub-area.
        if "/api/" in p:
            return ArchitectureLayer.API
        if "/pages/" in p or "/components/" in p:
            return ArchitectureLayer.FRONTEND
        return ArchitectureLayer.FRONTEND
    if "/api/" in p or "/routes/" in p or "/controllers/" in p:
        return ArchitectureLayer.API
    if "/services/" in p:
        return ArchitectureLayer.SERVICE
    if "/models/" in p:
        return ArchitectureLayer.MODEL
    if "/schemas/" in p:
        return ArchitectureLayer.SCHEMA
    if "/repositories/" in p or "/repository/" in p or "/db/" in p:
        return ArchitectureLayer.REPOSITORY
    if "/utils/" in p or "/helpers/" in p or "/core/" in p:
        return ArchitectureLayer.UTILITY
    if is_config:
        return ArchitectureLayer.CONFIGURATION
    if "/backend/" in p:
        return ArchitectureLayer.BACKEND
    return ArchitectureLayer.OTHER


def scan_tree(root_path: str, max_files: int = 5000) -> list[ScannedFile]:
    """Return the classified file inventory for a repository root."""
    root = os.path.abspath(root_path)
    files: list[ScannedFile] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in place.
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.endswith(".egg-info")]
        for fname in filenames:
            if fname.startswith(".") and fname not in {".env.example"}:
                continue
            abs_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(abs_path, root)
            language = detect_language(fname)
            ext = os.path.splitext(fname)[1].lstrip(".")
            is_generated = fname in GENERATED_NAMES or fname.endswith(GENERATED_SUFFIXES)
            is_config = fname in CONFIG_NAMES or language in CONFIG_LANGS
            is_test = _is_test(rel_path, fname)
            layer = detect_layer(rel_path, language, is_test, is_config)
            try:
                size = os.path.getsize(abs_path)
            except OSError:  # pragma: no cover
                size = 0
            files.append(
                ScannedFile(
                    path=rel_path,
                    abs_path=abs_path,
                    name=fname,
                    extension=ext,
                    language=language,
                    size_bytes=size,
                    module_path=os.path.dirname(rel_path) or ".",
                    layer=layer,
                    is_config=is_config,
                    is_generated=is_generated,
                    is_test=is_test,
                    parseable=(language in PARSEABLE and not is_generated and size < 500_000),
                )
            )
            if len(files) >= max_files:
                return files
    return files
