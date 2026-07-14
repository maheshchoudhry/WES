"""Parser + scanner unit tests (Sprint 12)."""

from app.domain.repository_enums import Language, SymbolType
from app.services.repo_parser import detect_language, parse
from app.services.repo_scanner import detect_layer, scan_tree

PY = '''
import os
from app.models import Base

MAX_RETRIES = 3  # TODO: make configurable

class User(Base):
    """A user model."""

    def save(self) -> None:
        pass


@router.get("/users")
def list_users():
    return []


async def helper(x: int) -> int:
    return x
'''


def test_detect_language():
    assert detect_language("main.py") == Language.PYTHON
    assert detect_language("App.tsx") == Language.TYPESCRIPT
    assert detect_language("index.js") == Language.JAVASCRIPT
    assert detect_language("package.json") == Language.JSON
    assert detect_language("Dockerfile") == Language.DOCKERFILE
    assert detect_language("requirements.txt") == Language.REQUIREMENTS
    assert detect_language("schema.sql") == Language.SQL
    assert detect_language("README.md") == Language.MARKDOWN


def test_python_symbols():
    r = parse("users.py", PY)
    names = {(s.name, s.symbol_type) for s in r.symbols}
    assert ("User", SymbolType.MODEL) in names  # subclass of Base -> model
    assert ("save", SymbolType.METHOD) in names
    assert ("list_users", SymbolType.ROUTE) in names  # @router.get -> route
    assert ("helper", SymbolType.FUNCTION) in names
    assert ("MAX_RETRIES", SymbolType.CONSTANT) in names


def test_python_imports_and_relationships():
    r = parse("users.py", PY)
    targets = {(i.target, i.external) for i in r.imports}
    assert ("os", True) in targets
    assert ("app.models", False) in targets  # internal
    assert ("User", "Base", "inherits") in r.relationships


def test_python_docstring_and_signature():
    r = parse("users.py", PY)
    user = next(s for s in r.symbols if s.name == "User")
    assert user.docstring == "A user model."
    save = next(s for s in r.symbols if s.name == "save")
    assert "save(self)" in save.signature


def test_python_todos():
    r = parse("users.py", PY)
    assert any(t.tag == "TODO" and "configurable" in t.text for t in r.todos)


def test_typescript_symbols():
    ts = (
        'import { useState } from "react";\n'
        'import { http } from "./client";\n'
        "export interface Provider { id: string; }\n"
        "export type Role = string;\n"
        "export function ProviderSettings() { return null; }\n"
        "export const helper = () => 1;\n"
    )
    r = parse("ProviderSettings.tsx", ts)
    by = {s.name: s.symbol_type for s in r.symbols}
    assert by["Provider"] == SymbolType.INTERFACE
    assert by["Role"] == SymbolType.TYPE
    assert by["ProviderSettings"] == SymbolType.COMPONENT  # PascalCase in .tsx
    imports = {(i.target, i.external) for i in r.imports}
    assert ("react", True) in imports and ("./client", False) in imports


def test_package_json_and_requirements():
    pj = parse(
        "package.json", '{"dependencies": {"react": "18"}, "devDependencies": {"vite": "6"}}'
    )
    assert {i.target for i in pj.imports} == {"react", "vite"}
    req = parse("requirements.txt", "fastapi==0.115.6\n# comment\nhttpx==0.28.1\n")
    assert {i.target for i in req.imports} == {"fastapi", "httpx"}


def test_sql_and_dockerfile():
    sql = parse(
        "schema.sql", "CREATE TABLE users (id int);\nCREATE TABLE IF NOT EXISTS posts (id int);"
    )
    tables = {s.name for s in sql.symbols if s.symbol_type == SymbolType.MODEL}
    assert tables == {"users", "posts"}
    docker = parse("Dockerfile", "FROM python:3.13\nRUN pip install fastapi")
    assert any(i.target.startswith("python") for i in docker.imports)


def test_malformed_python_does_not_raise():
    r = parse("broken.py", "def (: this is not valid python")
    assert r.symbols == []  # gracefully empty, no exception


def test_detect_layer():
    assert (
        detect_layer("backend/app/services/x.py", Language.PYTHON, False, False).value == "service"
    )
    assert detect_layer("backend/app/models/x.py", Language.PYTHON, False, False).value == "model"
    assert detect_layer("backend/app/api/v1/x.py", Language.PYTHON, False, False).value == "api"
    assert (
        detect_layer("frontend/src/pages/X.tsx", Language.TYPESCRIPT, False, False).value
        == "frontend"
    )
    assert detect_layer("backend/tests/test_x.py", Language.PYTHON, True, False).value == "test"
    assert detect_layer("docs/readme.md", Language.MARKDOWN, False, False).value == "documentation"


def test_scanner_ignores_and_classifies(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("x = 1\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("junk")
    (tmp_path / "package.json").write_text('{"name":"x"}')
    (tmp_path / "yarn.lock").write_text("locked")
    files = scan_tree(str(tmp_path))
    paths = {f.path for f in files}
    assert "app/main.py" in paths
    assert not any("node_modules" in p for p in paths)  # ignored dir pruned
    lock = next(f for f in files if f.name == "yarn.lock")
    assert lock.is_generated
    pkg = next(f for f in files if f.name == "package.json")
    assert pkg.is_config
