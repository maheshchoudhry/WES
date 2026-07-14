"""Code parser (Sprint 12).

Extracts symbols, imports, routes, models, TODOs, and doc headings from real
source files. Python is parsed with the standard-library ``ast`` (accurate);
TypeScript/JavaScript and config formats use focused, dependency-free parsing.
All functions are pure (operate on file content) so they are trivially testable.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field

from app.domain.repository_enums import Language, SymbolType

# Filenames / suffixes → language.
_EXT_LANG = {
    ".py": Language.PYTHON,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".json": Language.JSON,
    ".yaml": Language.YAML,
    ".yml": Language.YAML,
    ".md": Language.MARKDOWN,
    ".sql": Language.SQL,
}
_NAME_LANG = {
    "dockerfile": Language.DOCKERFILE,
    "requirements.txt": Language.REQUIREMENTS,
    "package.json": Language.JSON,
}

# Base classes that mark a class as an ORM model or a schema.
_MODEL_BASES = {"Base", "Model", "DeclarativeBase"}
_SCHEMA_BASES = {"BaseModel", "Schema", "TypedDict"}
_ROUTE_DECOS = {"get", "post", "put", "patch", "delete", "route", "websocket"}
_TODO_RE = re.compile(r"(?://|#|<!--|\*)\s*(TODO|FIXME|XXX|HACK)\b[:\s]*(.*)", re.IGNORECASE)


def detect_language(filename: str) -> Language:
    lower = filename.lower()
    if lower in _NAME_LANG:
        return _NAME_LANG[lower]
    if lower.startswith("dockerfile"):
        return Language.DOCKERFILE
    for ext, lang in _EXT_LANG.items():
        if lower.endswith(ext):
            return lang
    return Language.OTHER


@dataclass
class ParsedSymbol:
    name: str
    symbol_type: SymbolType
    line: int
    end_line: int | None = None
    parent: str | None = None
    signature: str | None = None
    docstring: str | None = None


@dataclass
class ParsedImport:
    target: str
    external: bool = False


@dataclass
class ParsedTodo:
    line: int
    tag: str
    text: str


@dataclass
class ParseResult:
    symbols: list[ParsedSymbol] = field(default_factory=list)
    imports: list[ParsedImport] = field(default_factory=list)
    relationships: list[tuple[str, str, str]] = field(default_factory=list)  # (src, tgt, type)
    todos: list[ParsedTodo] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    line_count: int = 0


def _extract_todos(content: str) -> list[ParsedTodo]:
    todos = []
    for i, line in enumerate(content.splitlines(), start=1):
        m = _TODO_RE.search(line)
        if m:
            todos.append(ParsedTodo(line=i, tag=m.group(1).upper(), text=m.group(2).strip()[:300]))
    return todos


def parse(filename: str, content: str, language: Language | None = None) -> ParseResult:
    lang = language or detect_language(filename)
    result = ParseResult(line_count=content.count("\n") + (1 if content else 0))
    result.todos = _extract_todos(content)
    try:
        if lang == Language.PYTHON:
            _parse_python(content, result)
        elif lang in (Language.TYPESCRIPT, Language.JAVASCRIPT):
            _parse_ts_js(filename, content, result)
        elif filename.lower() == "package.json":
            _parse_package_json(content, result)
        elif lang == Language.REQUIREMENTS:
            _parse_requirements(content, result)
        elif lang == Language.DOCKERFILE:
            _parse_dockerfile(content, result)
        elif lang == Language.SQL:
            _parse_sql(content, result)
        elif lang == Language.MARKDOWN:
            _parse_markdown(content, result)
    except Exception:  # pragma: no cover - a malformed file must not break a scan
        pass
    return result


# --- Python (ast) -------------------------------------------------------


def _py_signature(node) -> str:
    try:
        args = ast.unparse(node.args)
    except Exception:  # pragma: no cover
        args = ""
    return f"{node.name}({args})"


def _route_from_decorators(node) -> str | None:
    for deco in node.decorator_list:
        target = deco.func if isinstance(deco, ast.Call) else deco
        if isinstance(target, ast.Attribute) and target.attr in _ROUTE_DECOS:
            return target.attr.upper()
    return None


def _parse_python(content: str, result: ParseResult) -> None:
    tree = ast.parse(content)

    def visit(node, parent: str | None):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                bases = [b.id for b in child.bases if isinstance(b, ast.Name)]
                stype = SymbolType.CLASS
                if any(b in _MODEL_BASES for b in bases):
                    stype = SymbolType.MODEL
                elif any(b in _SCHEMA_BASES for b in bases):
                    stype = SymbolType.SCHEMA
                elif "Enum" in bases:
                    stype = SymbolType.ENUM
                result.symbols.append(
                    ParsedSymbol(
                        name=child.name,
                        symbol_type=stype,
                        line=child.lineno,
                        end_line=getattr(child, "end_lineno", None),
                        parent=parent,
                        signature=(
                            f"class {child.name}({', '.join(bases)})"
                            if bases
                            else f"class {child.name}"
                        ),
                        docstring=(ast.get_docstring(child) or None),
                    )
                )
                for base in bases:
                    result.relationships.append((child.name, base, "inherits"))
                visit(child, child.name)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                route = _route_from_decorators(child)
                stype = (
                    SymbolType.ROUTE
                    if route
                    else (SymbolType.METHOD if parent else SymbolType.FUNCTION)
                )
                result.symbols.append(
                    ParsedSymbol(
                        name=child.name,
                        symbol_type=stype,
                        line=child.lineno,
                        end_line=getattr(child, "end_lineno", None),
                        parent=parent,
                        signature=(
                            f"{route} {_py_signature(child)}" if route else _py_signature(child)
                        ),
                        docstring=(ast.get_docstring(child) or None),
                    )
                )
            elif isinstance(child, ast.Assign) and parent is None:
                for tgt in child.targets:
                    if isinstance(tgt, ast.Name) and tgt.id.isupper():
                        result.symbols.append(
                            ParsedSymbol(
                                name=tgt.id, symbol_type=SymbolType.CONSTANT, line=child.lineno
                            )
                        )

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.imports.append(
                    ParsedImport(target=alias.name, external=not alias.name.startswith("app"))
                )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            external = not (mod.startswith("app") or node.level > 0)
            result.imports.append(ParsedImport(target=mod, external=external))
    visit(tree, None)


# --- TypeScript / JavaScript -------------------------------------------

_TS_IMPORT = re.compile(r"""import\s+(?:[\w*{},\s]+\s+from\s+)?['"]([^'"]+)['"]""")
_TS_REQUIRE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")
_TS_FUNC = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)")
_TS_CONST = re.compile(r"^\s*(?:export\s+)?const\s+([A-Za-z_]\w*)\s*=")
_TS_CLASS = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_]\w*)")
_TS_INTERFACE = re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_]\w*)")
_TS_TYPE = re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z_]\w*)\s*=")


def _parse_ts_js(filename: str, content: str, result: ParseResult) -> None:
    is_tsx = filename.lower().endswith((".tsx", ".jsx"))
    for target in set(_TS_IMPORT.findall(content) + _TS_REQUIRE.findall(content)):
        result.imports.append(ParsedImport(target=target, external=not target.startswith(".")))
    for i, line in enumerate(content.splitlines(), start=1):
        if m := _TS_CLASS.match(line):
            result.symbols.append(
                ParsedSymbol(m.group(1), SymbolType.CLASS, i, signature=line.strip()[:200])
            )
        elif m := _TS_INTERFACE.match(line):
            result.symbols.append(ParsedSymbol(m.group(1), SymbolType.INTERFACE, i))
        elif m := _TS_TYPE.match(line):
            result.symbols.append(ParsedSymbol(m.group(1), SymbolType.TYPE, i))
        elif m := _TS_FUNC.match(line):
            name = m.group(1)
            stype = SymbolType.COMPONENT if is_tsx and name[:1].isupper() else SymbolType.FUNCTION
            result.symbols.append(ParsedSymbol(name, stype, i, signature=line.strip()[:200]))
        elif m := _TS_CONST.match(line):
            name = m.group(1)
            stype = SymbolType.COMPONENT if is_tsx and name[:1].isupper() else SymbolType.CONSTANT
            result.symbols.append(ParsedSymbol(name, stype, i))


# --- Config / data formats ---------------------------------------------


def _parse_package_json(content: str, result: ParseResult) -> None:
    data = json.loads(content)
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        for pkg in data.get(section) or {}:
            result.imports.append(ParsedImport(target=pkg, external=True))


def _parse_requirements(content: str, result: ParseResult) -> None:
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = re.split(r"[=<>!~\[ ]", line)[0].strip()
        if pkg:
            result.imports.append(ParsedImport(target=pkg, external=True))


def _parse_dockerfile(content: str, result: ParseResult) -> None:
    for i, line in enumerate(content.splitlines(), start=1):
        s = line.strip()
        if s.upper().startswith("FROM "):
            image = s.split()[1]
            result.imports.append(ParsedImport(target=image, external=True))
            result.symbols.append(ParsedSymbol(image, SymbolType.CONSTANT, i, signature=s[:200]))


def _parse_sql(content: str, result: ParseResult) -> None:
    for m in re.finditer(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"'`]?(\w+)", content, re.IGNORECASE
    ):
        line = content[: m.start()].count("\n") + 1
        result.symbols.append(ParsedSymbol(m.group(1), SymbolType.MODEL, line, signature="table"))


def _parse_markdown(content: str, result: ParseResult) -> None:
    for line in content.splitlines():
        if line.startswith("#"):
            result.headings.append(line.lstrip("#").strip()[:200])
