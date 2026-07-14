"""Git sandbox + Git service for the Autonomous Development Engine (Sprint 13).

Every autonomous implementation runs in a REAL, isolated git repository created
under the configured workspace directory — never the WES, WORLD, or Blueprint
repositories. Git operations are real (subprocess ``git``): init, branch, atomic
commits (Conventional Commits), and diffs. The engine NEVER pushes and NEVER
merges — the Founder is the final authority.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid

from app.core.config import get_settings

# Paths that must never be modified by the engine, regardless of target.
FORBIDDEN_SEGMENTS = ("blueprint", "/world", "wes/blueprint")

_GIT_ENV = {
    "GIT_AUTHOR_NAME": "WES AI",
    "GIT_AUTHOR_EMAIL": "ai@wes.studio",
    "GIT_COMMITTER_NAME": "WES AI",
    "GIT_COMMITTER_EMAIL": "ai@wes.studio",
    "GIT_TERMINAL_PROMPT": "0",
}


class SandboxError(RuntimeError):
    pass


def _run(args: list[str], cwd: str, check: bool = True) -> subprocess.CompletedProcess:
    env = {**os.environ, **_GIT_ENV}
    proc = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)
    if check and proc.returncode != 0:
        raise SandboxError(f"git {' '.join(args[1:])} failed: {proc.stderr.strip()[:300]}")
    return proc


class DevWorkspace:
    """Creates and guards per-task git sandboxes."""

    def __init__(self):
        self.base = os.path.abspath(get_settings().dev_workspace_dir)

    def _assert_safe(self, path: str) -> None:
        real = os.path.abspath(path)
        if not real.startswith(self.base + os.sep) and real != self.base:
            raise SandboxError("Refusing to operate outside the development workspace")
        low = real.lower()
        if any(seg in low for seg in FORBIDDEN_SEGMENTS):
            raise SandboxError("Refusing to touch a protected path (Blueprint/WORLD)")

    def create(self, task_code: str) -> str:
        """Initialize a fresh sandbox git repo on ``main`` and return its path."""
        os.makedirs(self.base, exist_ok=True)
        path = os.path.join(self.base, f"{task_code}-{uuid.uuid4().hex[:8]}")
        self._assert_safe(path)
        if os.path.exists(path):  # pragma: no cover - uuid collision
            shutil.rmtree(path)
        os.makedirs(path)
        git = GitService(path)
        git.init()
        return path

    def cleanup(self, path: str) -> None:
        self._assert_safe(path)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)


class GitService:
    """Real git operations, scoped to one sandbox path. Never pushes or merges."""

    def __init__(self, path: str):
        self.path = os.path.abspath(path)

    def _assert_within(self, rel_path: str) -> str:
        target = os.path.abspath(os.path.join(self.path, rel_path))
        if not target.startswith(self.path + os.sep):
            raise SandboxError(f"Path '{rel_path}' escapes the sandbox")
        low = target.lower()
        if any(seg in low for seg in FORBIDDEN_SEGMENTS):
            raise SandboxError("Refusing to write a protected path (Blueprint/WORLD)")
        return target

    # -- lifecycle ---------------------------------------------------------

    def init(self) -> None:
        _run(["git", "init", "-q", "-b", "main"], self.path, check=False)
        # Older git without -b: ensure branch.
        if self.current_branch() not in ("main", "master"):
            _run(["git", "checkout", "-q", "-b", "main"], self.path, check=False)
        readme = os.path.join(self.path, "README.md")
        with open(readme, "w", encoding="utf-8") as fh:
            fh.write("# Sandbox\n\nWES autonomous development sandbox.\n")
        _run(["git", "add", "-A"], self.path)
        _run(["git", "commit", "-q", "-m", "chore: initialize sandbox"], self.path)

    def create_branch(self, branch: str) -> str:
        _run(["git", "checkout", "-q", "-b", branch], self.path)
        return branch

    # -- file ops (guarded) ------------------------------------------------

    def write_file(self, rel_path: str, content: str) -> None:
        target = self._assert_within(rel_path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(content)

    def delete_file(self, rel_path: str) -> None:
        target = self._assert_within(rel_path)
        if os.path.exists(target):
            os.remove(target)

    def rename_file(self, old_rel: str, new_rel: str) -> None:
        src = self._assert_within(old_rel)
        dst = self._assert_within(new_rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(src):
            os.rename(src, dst)

    def read_file(self, rel_path: str) -> str | None:
        target = self._assert_within(rel_path)
        if not os.path.exists(target):
            return None
        with open(target, encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    # -- git queries / commits --------------------------------------------

    def stage_all(self) -> None:
        _run(["git", "add", "-A"], self.path)

    def commit(self, message: str) -> str:
        _run(["git", "commit", "-q", "-m", message], self.path)
        return self.head_sha()

    def head_sha(self) -> str:
        return _run(["git", "rev-parse", "HEAD"], self.path).stdout.strip()

    def current_branch(self) -> str:
        return _run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], self.path, check=False
        ).stdout.strip()

    def diff(self, base: str = "main") -> str:
        return _run(["git", "diff", f"{base}...HEAD"], self.path, check=False).stdout

    def diff_file(self, base: str, rel_path: str) -> str:
        return _run(
            ["git", "diff", f"{base}...HEAD", "--", rel_path], self.path, check=False
        ).stdout

    def shortstat(self, base: str = "main") -> dict:
        out = _run(["git", "diff", "--shortstat", f"{base}...HEAD"], self.path, check=False).stdout
        files = additions = deletions = 0
        import re

        if m := re.search(r"(\d+) files? changed", out):
            files = int(m.group(1))
        if m := re.search(r"(\d+) insertion", out):
            additions = int(m.group(1))
        if m := re.search(r"(\d+) deletion", out):
            deletions = int(m.group(1))
        return {"files_changed": files, "additions": additions, "deletions": deletions}

    def commit_count(self, base: str = "main") -> int:
        out = _run(["git", "rev-list", "--count", f"{base}..HEAD"], self.path, check=False).stdout
        return int(out.strip() or 0)

    def log(self, base: str = "main") -> list[str]:
        out = _run(
            ["git", "log", "--pretty=format:%s", f"{base}..HEAD"], self.path, check=False
        ).stdout
        return [line for line in out.splitlines() if line]
