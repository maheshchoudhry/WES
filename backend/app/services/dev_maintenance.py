"""Test-gated existing-code maintenance (WP1 — Stabilization Program).

Wires the :class:`CodeModificationEngine` to the real git sandbox and the real
test runner so an AI employee can *maintain* code that already exists, not just
scaffold new files:

    read existing file → AST-safe edit → write → commit → run tests →
        keep on green / hard-rollback on red

Every applied edit is recorded as a real ``GeneratedChange`` (``change_type`` =
MODIFY / RENAME / DELETE) carrying a real unified git diff. The sandbox guards
(``dev_git``) still forbid Blueprint/WORLD and any path escape.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.domain.development_enums import ChangeStatus, ChangeType
from app.models.development import GeneratedChange
from app.services.dev_git import GitService
from app.services.dev_modification import CodeModificationEngine, ModificationError
from app.services.dev_review import TestingService


@dataclass
class ModificationOutcome:
    ok: bool
    change_type: str
    path: str
    diff: str
    detail: str
    tests_passed: int = 0
    tests_failed: int = 0
    rolled_back: bool = False


# Supported edit operations against an existing file.
_OPS = {
    "add_function",
    "add_method",
    "replace_function",
    "remove_symbol",
    "rename_symbol",
    "insert_after_anchor",
    "insert_before_anchor",
}


class CodeMaintenanceService:
    """Apply a single AST-safe edit to an existing sandbox file, gated by tests."""

    def __init__(self, db: Session):
        self.db = db
        self.engine = CodeModificationEngine()

    def _apply_edit(self, source: str, op: str, params: dict) -> str:
        if op == "add_function":
            return self.engine.add_function(
                source,
                params["name"],
                params["source"],
                imports=params.get("imports"),
            )
        if op == "add_method":
            return self.engine.add_method(
                source, params["class_name"], params["name"], params["source"]
            )
        if op == "replace_function":
            return self.engine.replace_function(source, params["name"], params["source"])
        if op == "remove_symbol":
            return self.engine.remove_symbol(source, params["name"])
        if op == "rename_symbol":
            return self.engine.rename_symbol(source, params["old_name"], params["new_name"])
        if op == "insert_after_anchor":
            return self.engine.insert_after_anchor(
                source, params["anchor"], params["snippet"], occurrence=params.get("occurrence", 1)
            )
        if op == "insert_before_anchor":
            return self.engine.insert_before_anchor(
                source, params["anchor"], params["snippet"], occurrence=params.get("occurrence", 1)
            )
        raise ModificationError(f"unsupported operation '{op}'")

    def modify_file(
        self,
        *,
        task_id: uuid.UUID | None,
        git: GitService,
        rel_path: str,
        op: str,
        params: dict,
        base: str = "main",
        run_tests: bool = True,
        commit_message: str | None = None,
    ) -> ModificationOutcome:
        """Modify one existing file. Commits on success; hard-rolls-back on failure.

        Returns a :class:`ModificationOutcome`; also persists a ``GeneratedChange``
        when ``task_id`` is provided.
        """
        if op not in _OPS:
            raise ModificationError(f"unsupported operation '{op}'")
        original = git.read_file(rel_path)
        if original is None:
            raise ModificationError(f"file '{rel_path}' does not exist in the sandbox")

        checkpoint = git.head_sha()
        # 1. Compute the new content (raises ModificationError if unsafe/invalid).
        new_content = self._apply_edit(original, op, params)
        if new_content == original:
            return ModificationOutcome(
                ok=True,
                change_type=_change_type_for(op).value,
                path=rel_path,
                diff="",
                detail="no-op: source unchanged",
            )

        # 2. Write + rename/delete handling.
        if op == "rename_symbol":
            git.write_file(rel_path, new_content)
        elif op == "remove_symbol":
            git.write_file(rel_path, new_content)
        else:
            git.write_file(rel_path, new_content)
        git.stage_all()
        git.commit((commit_message or f"refactor: {op} in {rel_path}")[:100])
        diff = git.diff_file(base, rel_path)[:8000]

        # 3. Test gate (real py_compile + pytest). Roll back on failure.
        passed = failed = 0
        if run_tests:
            # Only Python files are byte-compiled; other languages (TSX/TS/JS) are
            # verified by the project's own test/build gate downstream.
            py_files = [rel_path] if rel_path.endswith(".py") else []
            runs = TestingService(self.db).run(task_id or uuid.uuid4(), git.path, py_files)
            passed = sum(r.passed_count for r in runs)
            failed = sum(
                r.failed_count
                for r in runs
                if (r.status.value if hasattr(r.status, "value") else r.status) == "failed"
            )
            compile_failed = any(
                (r.kind.value if hasattr(r.kind, "value") else r.kind) == "compile"
                and (r.status.value if hasattr(r.status, "value") else r.status) == "failed"
                for r in runs
            )
            if failed or compile_failed:
                git.rollback_to(checkpoint)
                self._record(task_id, rel_path, op, params, diff, ChangeStatus.REVERTED)
                return ModificationOutcome(
                    ok=False,
                    change_type=_change_type_for(op).value,
                    path=rel_path,
                    diff=diff,
                    detail=f"tests failed ({failed} failing); rolled back to {checkpoint[:8]}",
                    tests_passed=passed,
                    tests_failed=failed,
                    rolled_back=True,
                )

        self._record(task_id, rel_path, op, params, diff, ChangeStatus.APPLIED)
        return ModificationOutcome(
            ok=True,
            change_type=_change_type_for(op).value,
            path=rel_path,
            diff=diff,
            detail=f"applied {op}; {passed} tests passed",
            tests_passed=passed,
            tests_failed=failed,
        )

    def _record(
        self,
        task_id: uuid.UUID | None,
        rel_path: str,
        op: str,
        params: dict,
        diff: str,
        status: ChangeStatus,
    ) -> None:
        if task_id is None:
            return
        old_path = params.get("old_name_path")
        self.db.add(
            GeneratedChange(
                task_id=task_id,
                path=rel_path,
                old_path=old_path,
                change_type=_change_type_for(op),
                language="python",
                content=None,
                diff=diff,
                rationale=f"Existing-code {op} ({', '.join(sorted(params))}).",
                status=status,
                sequence=99,
            )
        )
        self.db.flush()


def _change_type_for(op: str) -> ChangeType:
    if op == "remove_symbol":
        return ChangeType.DELETE
    if op == "rename_symbol":
        return ChangeType.MODIFY
    return ChangeType.MODIFY
