"""Review engines for the Quality Gate Engine (Sprint 14).

Each engine analyzes the REAL generated code (from Sprint 13's generated_changes)
and returns structured findings. Python is analyzed with the standard-library
``ast`` (accurate); other signals use focused regex. Engines are pure — they take
a list of change dicts ``{path, language, content}`` and return ``Finding``s — so
they are trivially testable and deterministic.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from app.domain.quality_enums import (
    DependencyCategory,
    DocumentationCategory,
    FindingSeverity,
    PerformanceCategory,
    ReviewCategory,
    SecurityCategory,
)


@dataclass
class Finding:
    engine: str  # architecture | code | security | performance | dependency | documentation
    category: str
    severity: FindingSeverity
    message: str
    file_path: str | None = None
    line: int | None = None
    package: str | None = None
    cwe: str | None = None


_SECRET_RE = re.compile(
    r"""(password|passwd|api_key|apikey|secret|token|access_key)\s*=\s*['"][^'"]{6,}['"]""",
    re.IGNORECASE,
)
_DEPRECATED_PKGS = {"imp", "distutils", "asyncore", "cgi", "nose"}


def _python_files(changes: list[dict]) -> list[dict]:
    return [c for c in changes if (c.get("language") == "python") and c.get("content")]


def _parse(content: str):
    try:
        return ast.parse(content)
    except SyntaxError:
        return None


class ArchitectureReviewService:
    """Layer violations, circular deps, patterns, naming, folder standards."""

    def analyze(self, changes: list[dict]) -> list[Finding]:
        findings: list[Finding] = []
        import_map: dict[str, set[str]] = {}
        for c in _python_files(changes):
            tree = _parse(c["content"])
            if tree is None:
                continue
            stem = c["path"].rsplit("/", 1)[-1].rsplit(".", 1)[0]
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not re.match(
                    r"^[A-Z][A-Za-z0-9]*$", node.name
                ):
                    findings.append(
                        Finding(
                            "architecture",
                            ReviewCategory.NAMING.value,
                            FindingSeverity.LOW,
                            f"Class '{node.name}' should be PascalCase",
                            c["path"],
                            node.lineno,
                        )
                    )
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not re.match(
                    r"^_?[a-z][a-z0-9_]*$", node.name
                ):
                    findings.append(
                        Finding(
                            "architecture",
                            ReviewCategory.NAMING.value,
                            FindingSeverity.LOW,
                            f"Function '{node.name}' should be snake_case",
                            c["path"],
                            node.lineno,
                        )
                    )
                if isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.rsplit(".", 1)[-1])
            import_map[stem] = imports
        # Circular dependency within the change set.
        for a, deps in import_map.items():
            for b in deps:
                if b in import_map and a in import_map.get(b, set()):
                    findings.append(
                        Finding(
                            "architecture",
                            ReviewCategory.CIRCULAR_DEPENDENCY.value,
                            FindingSeverity.HIGH,
                            f"Circular import between {a} and {b}",
                        )
                    )
        return findings


class CodeReviewService:
    """Complexity, maintainability, dead code, duplication, standards, errors, logging."""

    def analyze(self, changes: list[dict]) -> list[Finding]:
        findings: list[Finding] = []
        for c in _python_files(changes):
            content = c["content"]
            lines = content.splitlines()
            path = c["path"]
            if len(lines) > 300:
                findings.append(
                    Finding(
                        "code",
                        ReviewCategory.MAINTAINABILITY.value,
                        FindingSeverity.MEDIUM,
                        f"File is long ({len(lines)} lines)",
                        path,
                        1,
                    )
                )
            for i, line in enumerate(lines, 1):
                if len(line) > 100:
                    findings.append(
                        Finding(
                            "code",
                            ReviewCategory.CODING_STANDARDS.value,
                            FindingSeverity.LOW,
                            "Line exceeds 100 characters",
                            path,
                            i,
                        )
                    )
                if line.strip() == "print()" or re.match(r"\s*print\(", line):
                    findings.append(
                        Finding(
                            "code",
                            ReviewCategory.LOGGING.value,
                            FindingSeverity.INFO,
                            "Use logging instead of print()",
                            path,
                            i,
                        )
                    )
            if re.search(r"except\s*:", content):
                findings.append(
                    Finding(
                        "code",
                        ReviewCategory.ERROR_HANDLING.value,
                        FindingSeverity.MEDIUM,
                        "Bare 'except:' — catch specific exceptions",
                        path,
                    )
                )
            tree = _parse(content)
            if tree is not None:
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        branches = sum(
                            1
                            for n in ast.walk(node)
                            if isinstance(n, (ast.If, ast.For, ast.While, ast.BoolOp, ast.Try))
                        )
                        if branches > 10:
                            findings.append(
                                Finding(
                                    "code",
                                    ReviewCategory.COMPLEXITY.value,
                                    FindingSeverity.MEDIUM,
                                    f"Function '{node.name}' is complex ({branches} branches)",
                                    path,
                                    node.lineno,
                                )
                            )
                        length = (
                            getattr(node, "end_lineno", node.lineno) or node.lineno
                        ) - node.lineno
                        if length > 50:
                            findings.append(
                                Finding(
                                    "code",
                                    ReviewCategory.MAINTAINABILITY.value,
                                    FindingSeverity.LOW,
                                    f"Function '{node.name}' is long ({length} lines)",
                                    path,
                                    node.lineno,
                                )
                            )
            # Duplicated code: 3+ identical non-trivial lines.
            seen: dict[str, int] = {}
            for line in lines:
                s = line.strip()
                if len(s) > 20 and not s.startswith("#"):
                    seen[s] = seen.get(s, 0) + 1
            for s, n in seen.items():
                if n >= 3:
                    findings.append(
                        Finding(
                            "code",
                            ReviewCategory.DUPLICATED_CODE.value,
                            FindingSeverity.LOW,
                            f"Duplicated line ({n}×): {s[:60]}",
                            path,
                        )
                    )
        return findings


class SecurityReviewService:
    """Secrets, SQL/command injection, path traversal, eval/exec."""

    def analyze(self, changes: list[dict]) -> list[Finding]:
        findings: list[Finding] = []
        for c in _python_files(changes):
            content = c["content"]
            path = c["path"]
            for i, line in enumerate(content.splitlines(), 1):
                if _SECRET_RE.search(line):
                    findings.append(
                        Finding(
                            "security",
                            SecurityCategory.SECRET.value,
                            FindingSeverity.CRITICAL,
                            "Possible hardcoded secret",
                            path,
                            i,
                            cwe="CWE-798",
                        )
                    )
                if re.search(r"execute\(\s*f['\"]", line) or re.search(
                    r"(SELECT|INSERT|UPDATE|DELETE).+(%|\+|\.format)", line, re.IGNORECASE
                ):
                    findings.append(
                        Finding(
                            "security",
                            SecurityCategory.SQL_INJECTION.value,
                            FindingSeverity.CRITICAL,
                            "Possible SQL injection (string-built query)",
                            path,
                            i,
                            cwe="CWE-89",
                        )
                    )
                if re.search(r"os\.system\(|shell\s*=\s*True|subprocess\.call\(.+shell", line):
                    findings.append(
                        Finding(
                            "security",
                            SecurityCategory.COMMAND_INJECTION.value,
                            FindingSeverity.CRITICAL,
                            "Possible command injection (shell execution)",
                            path,
                            i,
                            cwe="CWE-78",
                        )
                    )
                if re.search(r"\beval\(|\bexec\(", line):
                    findings.append(
                        Finding(
                            "security",
                            SecurityCategory.COMMAND_INJECTION.value,
                            FindingSeverity.HIGH,
                            "Use of eval/exec",
                            path,
                            i,
                            cwe="CWE-95",
                        )
                    )
                if re.search(r"open\(\s*f['\"].*\{", line):
                    findings.append(
                        Finding(
                            "security",
                            SecurityCategory.PATH_TRAVERSAL.value,
                            FindingSeverity.MEDIUM,
                            "Possible path traversal (interpolated path)",
                            path,
                            i,
                            cwe="CWE-22",
                        )
                    )
        return findings


class PerformanceReviewService:
    """Nested loops, DB calls in loops, large loops."""

    def analyze(self, changes: list[dict]) -> list[Finding]:
        findings: list[Finding] = []
        for c in _python_files(changes):
            tree = _parse(c["content"])
            path = c["path"]
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While)):
                    for inner in ast.walk(node):
                        if inner is not node and isinstance(inner, (ast.For, ast.While)):
                            findings.append(
                                Finding(
                                    "performance",
                                    PerformanceCategory.LARGE_LOOP.value,
                                    FindingSeverity.MEDIUM,
                                    "Nested loop — verify complexity",
                                    path,
                                    node.lineno,
                                )
                            )
                            break
                    for inner in ast.walk(node):
                        if isinstance(inner, ast.Call):
                            fn = getattr(inner.func, "attr", "") or getattr(inner.func, "id", "")
                            if fn in ("query", "execute", "scalar", "scalars", "get"):
                                findings.append(
                                    Finding(
                                        "performance",
                                        PerformanceCategory.DATABASE_CALLS.value,
                                        FindingSeverity.HIGH,
                                        f"Database call '{fn}()' inside a loop (N+1 risk)",
                                        path,
                                        node.lineno,
                                    )
                                )
                                break
        return findings


class DependencyReviewService:
    """Unused imports, deprecated packages, license/health signals."""

    def analyze(self, changes: list[dict]) -> list[Finding]:
        findings: list[Finding] = []
        for c in _python_files(changes):
            tree = _parse(c["content"])
            content = c["content"]
            path = c["path"]
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        if top in _DEPRECATED_PKGS:
                            findings.append(
                                Finding(
                                    "dependency",
                                    DependencyCategory.DEPRECATED.value,
                                    FindingSeverity.MEDIUM,
                                    f"Deprecated package '{top}'",
                                    path,
                                    node.lineno,
                                    package=top,
                                )
                            )
                        used_name = alias.asname or alias.name.split(".")[0]
                        if content.count(used_name) <= 1 and used_name != "annotations":
                            findings.append(
                                Finding(
                                    "dependency",
                                    DependencyCategory.UNUSED.value,
                                    FindingSeverity.LOW,
                                    f"Import '{used_name}' appears unused",
                                    path,
                                    node.lineno,
                                    package=used_name,
                                )
                            )
        return findings


class DocumentationReviewService:
    """Missing docstrings, API docs, knowledge-base + technical-doc presence."""

    def analyze(
        self, changes: list[dict], *, has_knowledge_doc: bool, has_markdown: bool
    ) -> list[Finding]:
        findings: list[Finding] = []
        for c in _python_files(changes):
            tree = _parse(c["content"])
            path = c["path"]
            if tree is None:
                continue
            if ast.get_docstring(tree) is None:
                findings.append(
                    Finding(
                        "documentation",
                        DocumentationCategory.MISSING_DOCS.value,
                        FindingSeverity.LOW,
                        "Module is missing a docstring",
                        path,
                        1,
                    )
                )
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if ast.get_docstring(node) is None and not node.name.startswith("test_"):
                        findings.append(
                            Finding(
                                "documentation",
                                DocumentationCategory.MISSING_DOCS.value,
                                FindingSeverity.LOW,
                                f"Function '{node.name}' is missing a docstring",
                                path,
                                node.lineno,
                            )
                        )
        # A committed markdown file is only one way to document a change. A
        # modification of an existing file (no scaffold) is documented by updating
        # the knowledge base instead — so only flag missing technical docs when
        # NEITHER a markdown change NOR a knowledge-base update is present.
        if not has_markdown and not has_knowledge_doc:
            findings.append(
                Finding(
                    "documentation",
                    DocumentationCategory.TECHNICAL_DOCS.value,
                    FindingSeverity.MEDIUM,
                    "No technical documentation file in the change",
                )
            )
        if not has_knowledge_doc:
            findings.append(
                Finding(
                    "documentation",
                    DocumentationCategory.KNOWLEDGE_BASE.value,
                    FindingSeverity.MEDIUM,
                    "Knowledge base was not updated for this task",
                )
            )
        return findings
