"""WP1 — Real Existing Code Modification Engine (Stabilization Program).

Proves that the engine modifies *existing* Python files safely: it adds/replaces/
removes/renames symbols while preserving surrounding code and imports, always emits
valid Python (AST-gated), and — through the maintenance service on a real git
sandbox — commits on green and hard-rolls-back on red.
"""

import ast

import pytest

from app.services.dev_git import GitService
from app.services.dev_maintenance import CodeMaintenanceService
from app.services.dev_modification import (
    CodeModificationEngine,
    ModificationError,
    index_symbols,
)

EXISTING = '''"""An existing module that predates the change."""

from __future__ import annotations

import math


ORIGINAL = "keep me"


def area(radius: float) -> float:
    """Existing behavior — must be preserved exactly."""
    return math.pi * radius * radius


class Shapes:
    """Existing class."""

    def perimeter(self, radius: float) -> float:
        return 2 * math.pi * radius
'''


@pytest.fixture
def mod_engine():
    return CodeModificationEngine()


# -- pure engine (AST) -------------------------------------------------------


def test_add_function_preserves_existing_code(mod_engine):
    new = mod_engine.add_function(
        EXISTING,
        "circumference",
        "def circumference(radius: float) -> float:\n"
        "    return 2 * math.pi * radius\n",
    )
    # New symbol present; every original symbol still present and unchanged.
    syms = index_symbols(new)
    assert "circumference" in syms.functions
    assert "area" in syms.functions and "Shapes" in syms.classes
    assert 'ORIGINAL = "keep me"' in new
    assert "Existing behavior — must be preserved exactly." in new
    ast.parse(new)  # valid Python


def test_add_function_merges_imports_without_duplication(mod_engine):
    new = mod_engine.add_function(
        EXISTING,
        "as_json",
        "def as_json() -> str:\n    return json.dumps({})\n",
        imports=["import json", "import math"],  # math already present
    )
    assert new.count("import math") == 1  # not duplicated
    assert "import json" in new
    ast.parse(new)


def test_add_function_rejects_duplicate_symbol(mod_engine):
    with pytest.raises(ModificationError):
        mod_engine.add_function(EXISTING, "area", "def area():\n    return 0\n")


def test_add_function_rejects_invalid_snippet(mod_engine):
    with pytest.raises(ModificationError):
        mod_engine.add_function(EXISTING, "broken", "def broken(:\n  pass")


def test_add_method_into_existing_class(mod_engine):
    new = mod_engine.add_method(
        EXISTING,
        "Shapes",
        "diameter",
        "def diameter(self, radius: float) -> float:\n    return 2 * radius\n",
    )
    syms = index_symbols(new)
    assert "diameter" in syms.methods["Shapes"]
    assert "perimeter" in syms.methods["Shapes"]  # original method kept
    ast.parse(new)


def test_replace_function_refactor_keeps_rest(mod_engine):
    new = mod_engine.replace_function(
        EXISTING,
        "area",
        "def area(radius: float) -> float:\n"
        "    # refactored implementation\n"
        "    return math.pi * radius ** 2\n",
    )
    assert "radius ** 2" in new
    assert "refactored implementation" in new
    # Untouched neighbors preserved.
    assert 'ORIGINAL = "keep me"' in new
    assert "class Shapes" in new
    ast.parse(new)


def test_remove_symbol(mod_engine):
    new = mod_engine.remove_symbol(EXISTING, "Shapes")
    syms = index_symbols(new)
    assert "Shapes" not in syms.classes
    assert "area" in syms.functions  # unrelated code untouched
    ast.parse(new)


def test_rename_symbol_updates_definition_and_references(mod_engine):
    src = (
        "def helper():\n    return 1\n\n\n"
        "def caller():\n    return helper() + helper()\n"
    )
    new = mod_engine.rename_symbol(src, "helper", "compute")
    syms = index_symbols(new)
    assert "compute" in syms.functions and "helper" not in syms.functions
    assert "def compute():" in new  # definition renamed
    assert "return compute() + compute()" in new  # both references updated
    assert "helper" not in new  # no trace of the old name anywhere
    ast.parse(new)


def test_rename_rejects_missing_symbol(mod_engine):
    with pytest.raises(ModificationError):
        mod_engine.rename_symbol(EXISTING, "does_not_exist", "x")


def test_every_output_is_valid_python(mod_engine):
    # Fuzz-ish: a chain of edits must never yield invalid source.
    src = EXISTING
    src = mod_engine.add_function(src, "f1", "def f1():\n    return 1\n")
    src = mod_engine.add_method(src, "Shapes", "m2", "def m2(self):\n    return 2\n")
    src = mod_engine.replace_function(src, "f1", "def f1():\n    return 11\n")
    src = mod_engine.rename_symbol(src, "f1", "f1_renamed")
    ast.parse(src)


# -- end-to-end on a real git sandbox with test-gated rollback ---------------


def _seed_sandbox(tmp_path) -> GitService:
    git = GitService(str(tmp_path))
    git.init()
    git.create_branch("feature/maintain")
    git.write_file("calc.py", EXISTING)
    git.write_file(
        "test_calc.py",
        "from calc import area\n\n\ndef test_area():\n    assert round(area(1), 2) == 3.14\n",
    )
    git.stage_all()
    git.commit("chore: seed existing module")
    return git


def test_maintenance_applies_and_commits_on_green(db_session, tmp_path):
    git = _seed_sandbox(tmp_path)
    checkpoint = git.head_sha()
    svc = CodeMaintenanceService(db_session)
    outcome = svc.modify_file(
        task_id=None,
        git=git,
        rel_path="calc.py",
        op="add_function",
        params={
            "name": "circumference",
            "source": "def circumference(radius: float) -> float:\n"
            "    return 2 * math.pi * radius\n",
        },
    )
    assert outcome.ok is True
    assert outcome.rolled_back is False
    assert "circumference" in (git.read_file("calc.py") or "")
    assert git.head_sha() != checkpoint  # a real new commit landed
    # Original test still present and code compiles.
    assert "def area" in (git.read_file("calc.py") or "")


def test_maintenance_rolls_back_on_failing_tests(db_session, tmp_path):
    git = _seed_sandbox(tmp_path)
    # Add a test that asserts a wrong result, so the modification's test gate fails.
    git.write_file(
        "test_regression.py",
        "from calc import area\n\n\ndef test_wrong():\n    assert area(1) == 999\n",
    )
    git.stage_all()
    git.commit("test: add a failing regression guard")
    checkpoint = git.head_sha()

    svc = CodeMaintenanceService(db_session)
    outcome = svc.modify_file(
        task_id=None,
        git=git,
        rel_path="calc.py",
        op="add_function",
        params={"name": "noop", "source": "def noop():\n    return None\n"},
    )
    assert outcome.ok is False
    assert outcome.rolled_back is True
    # Hard rollback: the sandbox is exactly back at the checkpoint, edit discarded.
    assert git.head_sha() == checkpoint
    assert "def noop" not in (git.read_file("calc.py") or "")


def test_maintenance_rejects_unsafe_edit_before_touching_disk(db_session, tmp_path):
    git = _seed_sandbox(tmp_path)
    checkpoint = git.head_sha()
    svc = CodeMaintenanceService(db_session)
    with pytest.raises(ModificationError):
        svc.modify_file(
            task_id=None,
            git=git,
            rel_path="calc.py",
            op="add_function",
            params={"name": "area", "source": "def area():\n    return 0\n"},  # duplicate
        )
    assert git.head_sha() == checkpoint  # nothing committed
