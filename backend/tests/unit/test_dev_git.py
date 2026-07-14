"""Git sandbox + generation unit tests (Sprint 13)."""

import ast

import pytest

from app.services.dev_generation import GenerationService, slugify
from app.services.dev_git import GitService, SandboxError


def test_git_init_branch_commit_diff(tmp_path):
    git = GitService(str(tmp_path))
    git.init()
    assert git.current_branch() == "main"
    git.create_branch("feature/x")
    assert git.current_branch() == "feature/x"

    git.write_file("mod.py", "def f():\n    return 1\n")
    git.write_file("test_mod.py", "from mod import f\n\ndef test_f():\n    assert f() == 1\n")
    git.stage_all()
    sha = git.commit("feat: add mod")
    assert len(sha) >= 7

    stat = git.shortstat("main")
    assert stat["files_changed"] == 2 and stat["additions"] > 0
    assert git.commit_count("main") == 1
    assert "feat: add mod" in git.log("main")
    diff = git.diff("main")
    assert "mod.py" in diff


def test_git_safety_rejects_escape(tmp_path):
    git = GitService(str(tmp_path))
    git.init()
    with pytest.raises(SandboxError):
        git.write_file("../escape.py", "x = 1")
    with pytest.raises(SandboxError):
        git.write_file("Blueprint/thing.py", "x = 1")


def test_slugify():
    assert slugify("Add Health Ping Utility") == "add_health_ping_utility"
    assert slugify("123 start").startswith("feature")
    assert slugify("") == "feature"


def test_generation_produces_valid_python(db_session):
    result = GenerationService(db_session).generate("Add Health Ping Utility")
    assert result.slug == "add_health_ping_utility"
    py = [c for c in result.changes if c.language == "python"]
    assert len(py) == 2
    for change in py:
        # Generated code must be syntactically valid.
        ast.parse(change.content)
    assert any(c.path.startswith("test_") for c in py)
    assert any(c.language == "markdown" for c in result.changes)
