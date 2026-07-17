"""Real existing-code modification engine (WP1 — Stabilization Program).

The Sprint-13 development engine could only *create* new scaffold files. To build
and *maintain* an evolving codebase (Project WORLD), the engine must safely modify
files that already exist: add functions/methods, refactor bodies, rename symbols,
and delete code — while preserving the surrounding code, imports, and formatting.

This module does exactly that, for Python, using the standard-library ``ast`` as a
correctness gate:

* every input is parsed first (reject invalid source),
* transformations are applied as *minimal textual edits* (insert / replace / remove
  specific line spans, or a validated word-boundary rename) so untouched code keeps
  its exact formatting,
* every output is re-parsed and MUST compile, otherwise the edit is rejected and the
  caller rolls back.

Nothing here writes to disk. The engine returns new file text; the git sandbox
(``dev_git.GitService``) performs the guarded write, and ``TestingService`` verifies
it — the caller rolls the sandbox back on any failure. Blueprint and WORLD are never
touched (the sandbox guards enforce that).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass


class ModificationError(ValueError):
    """Raised when a modification is unsafe or would produce invalid code."""


@dataclass
class ModuleSymbols:
    """A shallow index of a Python module's top-level + method symbols."""

    functions: list[str]
    classes: list[str]
    methods: dict[str, list[str]]  # class name -> method names
    imports: list[str]  # normalized "import x" / "from x import y" lines


def _validate(source: str, *, where: str) -> ast.Module:
    try:
        return ast.parse(source)
    except SyntaxError as exc:  # pragma: no cover - message content only
        raise ModificationError(f"{where}: source is not valid Python ({exc.msg})") from exc


def index_symbols(source: str) -> ModuleSymbols:
    """Return the top-level functions/classes/methods/imports of ``source``."""
    tree = _validate(source, where="index")
    functions: list[str] = []
    classes: list[str] = []
    methods: dict[str, list[str]] = {}
    imports: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
            methods[node.name] = [
                b.name
                for b in node.body
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                )
        elif isinstance(node, ast.ImportFrom):
            mod = ("." * (node.level or 0)) + (node.module or "")
            names = ", ".join(
                a.name + (f" as {a.asname}" if a.asname else "") for a in node.names
            )
            imports.append(f"from {mod} import {names}")
    return ModuleSymbols(functions, classes, methods, imports)


class CodeModificationEngine:
    """AST-guarded, formatting-preserving edits to existing Python source.

    Every method takes the *current* file text and returns the *new* file text.
    The output is guaranteed to parse; callers never see a broken file.
    """

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _lines(source: str) -> list[str]:
        return source.splitlines(keepends=True)

    @staticmethod
    def _ensure_trailing_newline(text: str) -> str:
        return text if text.endswith("\n") else text + "\n"

    def _import_insertion_line(self, tree: ast.Module) -> int:
        """1-based line AFTER which new imports should go (after the import block
        or the module docstring)."""
        last_import_end = 0
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                last_import_end = max(last_import_end, node.end_lineno or node.lineno)
        if last_import_end:
            return last_import_end
        # No imports: place after a module docstring if present, else at top.
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(
            getattr(tree.body[0], "value", None), ast.Constant
        ):
            return tree.body[0].end_lineno or 1
        return 0

    def _merge_imports(self, source: str, imports: list[str]) -> str:
        """Insert import lines that are not already present, in the import block."""
        wanted = [i.strip() for i in imports if i.strip()]
        if not wanted:
            return source
        existing = set(index_symbols(source).imports)
        new = [i for i in wanted if i not in existing]
        if not new:
            return source
        tree = _validate(source, where="merge_imports")
        at = self._import_insertion_line(tree)
        lines = self._lines(source)
        block = "".join(self._ensure_trailing_newline(i) for i in new)
        # __future__ imports must stay first; if we're inserting plain imports at the
        # very top (at == 0) and the first real statement is not an import, add a
        # blank separator so the file stays readable.
        insert_at = at  # number of leading lines to keep
        head = "".join(lines[:insert_at])
        tail = "".join(lines[insert_at:])
        merged = head + block + tail
        return self._finalize(source, merged, where="merge_imports")

    def _finalize(self, original: str, candidate: str, *, where: str) -> str:
        candidate = self._ensure_trailing_newline(candidate)
        _validate(candidate, where=where)  # MUST still be valid Python
        return candidate

    def _find_toplevel(self, tree: ast.Module, name: str):
        for node in tree.body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) and node.name == name:
                return node
        return None

    @staticmethod
    def _span_with_decorators(node) -> tuple[int, int]:
        """Return the inclusive 1-based (start, end) line span of a def/class,
        including any decorators above it."""
        start = node.lineno
        for dec in getattr(node, "decorator_list", []):
            start = min(start, dec.lineno)
        return start, node.end_lineno

    # -- operations --------------------------------------------------------

    def add_function(
        self, source: str, func_name: str, func_source: str, *, imports: list[str] | None = None
    ) -> str:
        """Append a new top-level function, preserving all existing code.

        Rejects if a top-level symbol ``func_name`` already exists (use
        :meth:`replace_function` to change an existing one).
        """
        _validate(source, where="add_function")
        if not func_name.isidentifier():
            raise ModificationError(f"'{func_name}' is not a valid identifier")
        snippet = _validate(func_source, where="add_function.snippet")
        if not any(
            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func_name
            for n in snippet.body
        ):
            raise ModificationError(
                f"new function source does not define a function named '{func_name}'"
            )
        if self._find_toplevel(_validate(source, where="add_function"), func_name):
            raise ModificationError(
                f"symbol '{func_name}' already exists; use replace_function to modify it"
            )
        working = self._merge_imports(source, imports or [])
        body = self._ensure_trailing_newline(func_source.strip("\n"))
        # Two blank lines before a top-level def (PEP 8), collapsing any trailing blanks.
        merged = working.rstrip("\n") + "\n\n\n" + body
        return self._finalize(source, merged, where="add_function")

    def add_method(
        self, source: str, class_name: str, method_name: str, method_source: str
    ) -> str:
        """Insert a new method at the end of an existing class body."""
        tree = _validate(source, where="add_method")
        cls = self._find_toplevel(tree, class_name)
        if not isinstance(cls, ast.ClassDef):
            raise ModificationError(f"class '{class_name}' not found")
        if any(
            isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) and b.name == method_name
            for b in cls.body
        ):
            raise ModificationError(
                f"method '{method_name}' already exists on '{class_name}'"
            )
        # Determine class body indentation from its first statement.
        first = cls.body[0]
        lines = self._lines(source)
        indent = re.match(r"[ \t]*", lines[first.lineno - 1]).group(0) or "    "
        # Re-indent the provided method source (which is written at column 0).
        dedented = method_source.strip("\n").splitlines()
        reindented = "\n".join((indent + ln if ln.strip() else "") for ln in dedented)
        insert_after = cls.body[-1].end_lineno  # after last class member
        head = "".join(lines[:insert_after])
        tail = "".join(lines[insert_after:])
        merged = head.rstrip("\n") + "\n\n" + reindented + "\n" + tail
        return self._finalize(source, merged, where="add_method")

    def replace_function(self, source: str, func_name: str, func_source: str) -> str:
        """Replace an existing top-level function's definition (refactor), keeping
        everything else byte-for-byte."""
        tree = _validate(source, where="replace_function")
        node = self._find_toplevel(tree, func_name)
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise ModificationError(f"function '{func_name}' not found")
        _validate(func_source, where="replace_function.snippet")
        start, end = self._span_with_decorators(node)
        lines = self._lines(source)
        head = "".join(lines[: start - 1])
        tail = "".join(lines[end:])
        body = self._ensure_trailing_newline(func_source.strip("\n"))
        merged = head + body + tail
        return self._finalize(source, merged, where="replace_function")

    def remove_symbol(self, source: str, name: str) -> str:
        """Delete a top-level function or class (with its decorators)."""
        tree = _validate(source, where="remove_symbol")
        node = self._find_toplevel(tree, name)
        if node is None:
            raise ModificationError(f"symbol '{name}' not found")
        start, end = self._span_with_decorators(node)
        lines = self._lines(source)
        # Also swallow one trailing blank-line separator, if present.
        while end < len(lines) and lines[end].strip() == "":
            end += 1
        merged = "".join(lines[: start - 1]) + "".join(lines[end:])
        return self._finalize(source, merged or "\n", where="remove_symbol")

    # -- language-agnostic anchored edits (TSX / TS / JS / etc.) -----------

    @staticmethod
    def _assert_balanced(snippet: str) -> None:
        """Reject a fragment whose brackets are internally unbalanced.

        Non-Python files have no stdlib AST here, so anchored insertions are
        sanity-checked for balanced (), [] and {} — a fragment that opens more
        than it closes (or vice-versa) would corrupt the host file. Real semantic
        validity is proven downstream by the build/test gate.
        """
        pairs = {")": "(", "]": "[", "}": "{"}
        openers = set(pairs.values())
        stack: list[str] = []
        in_str: str | None = None
        prev = ""
        for ch in snippet:
            if in_str:
                if ch == in_str and prev != "\\":
                    in_str = None
                prev = ch
                continue
            if ch in ("'", '"', "`"):
                in_str = ch
            elif ch in openers:
                stack.append(ch)
            elif ch in pairs:
                if not stack or stack[-1] != pairs[ch]:
                    raise ModificationError("snippet has unbalanced brackets")
                stack.pop()
            prev = ch
        if stack:
            raise ModificationError("snippet has unbalanced brackets")

    def insert_after_anchor(
        self, source: str, anchor: str, snippet: str, *, occurrence: int = 1
    ) -> str:
        """Insert ``snippet`` immediately after the line containing ``anchor``.

        Language-agnostic (used for ``.tsx`` and friends). The anchor must exist
        exactly ``occurrence`` times or more; the snippet is bracket-balance
        checked before insertion.
        """
        if anchor not in source:
            raise ModificationError(f"anchor not found: {anchor!r}")
        self._assert_balanced(snippet)
        lines = source.splitlines(keepends=True)
        seen = 0
        for i, line in enumerate(lines):
            if anchor in line:
                seen += 1
                if seen == occurrence:
                    block = self._ensure_trailing_newline(snippet)
                    lines.insert(i + 1, block)
                    return "".join(lines)
        raise ModificationError(f"anchor occurrence {occurrence} not found")

    def insert_before_anchor(
        self, source: str, anchor: str, snippet: str, *, occurrence: int = 1
    ) -> str:
        """Insert ``snippet`` immediately before the line containing ``anchor``."""
        if anchor not in source:
            raise ModificationError(f"anchor not found: {anchor!r}")
        self._assert_balanced(snippet)
        lines = source.splitlines(keepends=True)
        seen = 0
        for i, line in enumerate(lines):
            if anchor in line:
                seen += 1
                if seen == occurrence:
                    block = self._ensure_trailing_newline(snippet)
                    lines.insert(i, block)
                    return "".join(lines)
        raise ModificationError(f"anchor occurrence {occurrence} not found")

    def rename_symbol(self, source: str, old_name: str, new_name: str) -> str:
        """Rename an identifier across the whole module (definition + references).

        Uses a word-boundary replacement and then *proves* the result via AST: the
        old top-level symbol must be gone and the new one present, and the file must
        still parse. Rejected otherwise — no half-applied rename ever ships.
        """
        if not new_name.isidentifier():
            raise ModificationError(f"'{new_name}' is not a valid identifier")
        tree = _validate(source, where="rename_symbol")
        if self._find_toplevel(tree, old_name) is None:
            raise ModificationError(f"symbol '{old_name}' not found at module top level")
        if self._find_toplevel(tree, new_name) is not None:
            raise ModificationError(f"symbol '{new_name}' already exists")
        renamed = re.sub(rf"(?<![\w.])({re.escape(old_name)})(?![\w])", new_name, source)
        result = self._finalize(source, renamed, where="rename_symbol")
        after = index_symbols(result)
        if new_name not in (after.functions + after.classes):
            raise ModificationError("rename did not produce the expected new symbol")
        if old_name in (after.functions + after.classes):
            raise ModificationError("rename left the old symbol behind")
        return result
