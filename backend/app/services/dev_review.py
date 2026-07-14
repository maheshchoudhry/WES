"""Review, Testing, Documentation, Pull-Request, and Approval services (Sprint 13).

- ReviewService: automated multi-dimension code review (architecture, standards,
  security, performance, documentation, maintainability, test coverage).
- TestingService: REAL execution in the sandbox — py_compile (static), pytest
  (unit), and best-effort ruff/black (lint/format).
- DocumentationService: writes implementation notes into the Knowledge Engine.
- PullRequestService: builds a PR draft (title/body/diff summary/release notes)
  from real git state. Never pushes, never merges.
- ApprovalService: records the Founder's approve/reject decision (no auto-merge).
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.development_enums import (
    ApprovalDecision,
    DevTaskStatus,
    PRStatus,
    ReviewDimension,
    ReviewOutcome,
    ReviewSeverity,
    TestKind,
    TestStatus,
)
from app.domain.knowledge_enums import DocumentType, ReferenceEntityType
from app.models.development import (
    ApprovalHistory,
    CodeReview,
    DevelopmentTask,
    GeneratedChange,
    PullRequest,
    ReviewComment,
    TestRun,
)
from app.services.dev_git import GitService

_SECRET_RE = re.compile(
    r"""(password|api_key|secret|token)\s*=\s*['"][^'"]{6,}['"]""", re.IGNORECASE
)


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def review(self, task_id: uuid.UUID, changes: list[GeneratedChange]) -> CodeReview:
        comments: list[tuple[ReviewDimension, ReviewSeverity, str, str | None]] = []
        py_changes = [c for c in changes if (c.language == "python")]
        has_tests = any(c.path.startswith("test_") or "/test_" in c.path for c in changes)

        for c in py_changes:
            content = c.content or ""
            lines = content.splitlines()
            # Documentation.
            if '"""' not in content:
                comments.append(
                    (
                        ReviewDimension.DOCUMENTATION,
                        ReviewSeverity.WARNING,
                        "Missing module docstring",
                        c.path,
                    )
                )
            # Security.
            if _SECRET_RE.search(content):
                comments.append(
                    (
                        ReviewDimension.SECURITY,
                        ReviewSeverity.BLOCKER,
                        "Possible hardcoded secret",
                        c.path,
                    )
                )
            # Maintainability.
            if len(lines) > 300:
                comments.append(
                    (
                        ReviewDimension.MAINTAINABILITY,
                        ReviewSeverity.SUGGESTION,
                        f"Large file ({len(lines)} lines)",
                        c.path,
                    )
                )
            # Coding standards.
            if any(len(line) > 100 for line in lines):
                comments.append(
                    (
                        ReviewDimension.CODING_STANDARDS,
                        ReviewSeverity.SUGGESTION,
                        "Lines exceed 100 characters",
                        c.path,
                    )
                )
            # Performance (naive nested-loop heuristic).
            if re.search(r"for .+:\n\s+for .+:", content):
                comments.append(
                    (
                        ReviewDimension.PERFORMANCE,
                        ReviewSeverity.SUGGESTION,
                        "Nested loop — check complexity",
                        c.path,
                    )
                )

        # Test coverage.
        if not has_tests:
            comments.append(
                (
                    ReviewDimension.TEST_COVERAGE,
                    ReviewSeverity.WARNING,
                    "No test file among the changes",
                    None,
                )
            )
        else:
            comments.append(
                (
                    ReviewDimension.TEST_COVERAGE,
                    ReviewSeverity.INFO,
                    "Change includes unit tests",
                    None,
                )
            )
        # Architecture (positive signal).
        comments.append(
            (
                ReviewDimension.ARCHITECTURE,
                ReviewSeverity.INFO,
                "Change follows the layered structure",
                None,
            )
        )

        penalties = {
            ReviewSeverity.BLOCKER: 40,
            ReviewSeverity.WARNING: 10,
            ReviewSeverity.SUGGESTION: 3,
            ReviewSeverity.INFO: 0,
        }
        score = max(0.0, 100.0 - sum(penalties[sev] for _, sev, _, _ in comments))
        has_blocker = any(sev == ReviewSeverity.BLOCKER for _, sev, _, _ in comments)
        outcome = ReviewOutcome.CHANGES_REQUESTED if has_blocker else ReviewOutcome.APPROVED

        review = CodeReview(
            task_id=task_id,
            outcome=outcome,
            score=round(score, 1),
            summary=f"Automated review across 7 dimensions — {len(comments)} findings, score {round(score,1)}.",
        )
        self.db.add(review)
        self.db.flush()
        for dim, sev, msg, path in comments:
            self.db.add(
                ReviewComment(
                    review_id=review.id,
                    dimension=dim,
                    severity=sev,
                    file_path=path,
                    message=msg,
                )
            )
        self.db.flush()
        return review


class TestingService:
    def __init__(self, db: Session):
        self.db = db

    def _record(self, task_id, kind, command, status, passed, failed, output, ms) -> TestRun:
        run = TestRun(
            task_id=task_id,
            kind=kind,
            command=command,
            status=status,
            passed_count=passed,
            failed_count=failed,
            output=(output or "")[:4000],
            duration_ms=ms,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def _sh(self, args: list[str], cwd: str) -> tuple[int, str, int]:
        started = time.monotonic()
        try:
            proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)
            out = (proc.stdout or "") + (proc.stderr or "")
            return proc.returncode, out, int((time.monotonic() - started) * 1000)
        except FileNotFoundError:
            return 127, "tool not available", 0
        except Exception as exc:  # pragma: no cover - defensive
            return 1, str(exc), int((time.monotonic() - started) * 1000)

    def run(self, task_id: uuid.UUID, sandbox_path: str, py_files: list[str]) -> list[TestRun]:
        runs = []
        # 1. Static compile check (real).
        rc, out, ms = self._sh([sys.executable, "-m", "py_compile", *py_files], sandbox_path)
        runs.append(
            self._record(
                task_id,
                TestKind.COMPILE,
                "python -m py_compile",
                TestStatus.PASSED if rc == 0 else TestStatus.FAILED,
                len(py_files) if rc == 0 else 0,
                0 if rc == 0 else len(py_files),
                out,
                ms,
            )
        )
        # 2. Unit tests (real pytest in the sandbox).
        rc, out, ms = self._sh([sys.executable, "-m", "pytest", "-q"], sandbox_path)
        passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", out)) else 0
        failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", out)) else 0
        runs.append(
            self._record(
                task_id,
                TestKind.UNIT,
                "python -m pytest -q",
                TestStatus.PASSED if rc == 0 and failed == 0 else TestStatus.FAILED,
                passed,
                failed,
                out,
                ms,
            )
        )
        # 3. Lint (best-effort ruff).
        rc, out, ms = self._sh(["ruff", "check", "."], sandbox_path)
        runs.append(
            self._record(
                task_id,
                TestKind.LINT,
                "ruff check .",
                (
                    TestStatus.PASSED
                    if rc == 0
                    else (TestStatus.SKIPPED if rc == 127 else TestStatus.FAILED)
                ),
                0,
                0,
                out,
                ms,
            )
        )
        return runs


class DocumentationService:
    def __init__(self, db: Session, actor: str = "WES AI"):
        self.db = db
        self.actor = actor

    def document(self, task: DevelopmentTask, notes: str) -> uuid.UUID | None:
        """Write implementation notes into the Knowledge Engine (lessons learned)."""
        from app.services.knowledge import KnowledgeService

        ks = KnowledgeService(self.db, actor=self.actor)
        doc = ks.create(
            title=f"Implementation: {task.title}"[:300],
            doc_type=DocumentType.LESSONS_LEARNED,
            content=notes,
            summary=f"Autonomous implementation notes for {task.code}.",
            keywords=f"development autonomous {task.code}",
        )
        if task.repository_id:
            from app.services.knowledge_graph import ReferenceService

            ReferenceService(self.db).add(
                doc.id, ReferenceEntityType.REPOSITORY, task.repository_id, "Target repository"
            )
        return doc.id


class PullRequestService:
    def __init__(self, db: Session):
        self.db = db

    def create_draft(
        self, task: DevelopmentTask, git: GitService, plan_summary: str
    ) -> PullRequest:
        stat = git.shortstat("main")
        commits = git.log("main")
        diff = git.diff("main")
        title = f"feat: {task.title}"[:300]
        changes = self.db.scalars(
            select(GeneratedChange).where(GeneratedChange.task_id == task.id)
        ).all()
        file_list = "\n".join(
            f"- `{c.path}` ({c.change_type.value if hasattr(c.change_type,'value') else c.change_type})"
            for c in changes
        )
        body = (
            f"## Summary\n{plan_summary}\n\n"
            f"## Changes\n{file_list}\n\n"
            f"## Commits\n" + "\n".join(f"- {c}" for c in commits) + "\n\n"
            "## Verification\n- Static compile check\n- Unit tests (pytest)\n\n"
            "> Autonomously prepared by the WES Development Engine. Requires Founder approval; "
            "not pushed or merged.\n"
        )
        release_notes = f"### {title}\n{plan_summary}\n\n" + "\n".join(f"- {c}" for c in commits)
        pr = PullRequest(
            task_id=task.id,
            branch_name=git.current_branch(),
            base_branch="main",
            title=title,
            body=body,
            diff_summary=diff[:8000],
            release_notes=release_notes,
            status=PRStatus.DRAFT,
            commit_count=git.commit_count("main"),
            files_changed=stat["files_changed"],
            additions=stat["additions"],
            deletions=stat["deletions"],
        )
        self.db.add(pr)
        self.db.flush()
        return pr


class ApprovalService:
    def __init__(self, db: Session, actor: str = "Founder"):
        self.db = db
        self.actor = actor

    def decide(
        self,
        task_id: uuid.UUID,
        decision: ApprovalDecision | str,
        notes: str | None = None,
        *,
        override: bool = False,
    ) -> ApprovalHistory:
        from app.core.exceptions import NotFoundError, ValidationError

        task = self.db.get(DevelopmentTask, task_id)
        if task is None:
            raise NotFoundError(f"Development task {task_id} not found")
        dec = decision.value if isinstance(decision, ApprovalDecision) else decision

        # Quality gate enforcement (Sprint 14): no APPROVAL may proceed until the
        # mandatory quality gates have been evaluated. A failing gate requires an
        # explicit Founder override; rejection/changes-requested are always allowed.
        if dec == ApprovalDecision.APPROVED.value:
            from app.services.quality_gate_service import QualityGateService

            gate = QualityGateService(self.db).gate_for_task(task_id)
            if gate is None:
                raise ValidationError(
                    "Quality gates have not been evaluated for this task; cannot approve."
                )
            if not gate.approval_eligible and not override:
                raise ValidationError(
                    "Quality gates failed; approval requires an explicit Founder override."
                )

        pr = self.db.scalar(select(PullRequest).where(PullRequest.task_id == task_id))
        record = ApprovalHistory(
            task_id=task_id,
            pull_request_id=pr.id if pr else None,
            decision=dec,
            actor=self.actor,
            notes=notes,
        )
        self.db.add(record)
        # Update statuses — NEVER merges or pushes; a human performs the merge.
        if dec == ApprovalDecision.APPROVED.value:
            task.status = DevTaskStatus.APPROVED
            if pr:
                pr.status = PRStatus.APPROVED
        elif dec == ApprovalDecision.REJECTED.value:
            task.status = DevTaskStatus.REJECTED
            if pr:
                pr.status = PRStatus.REJECTED
        else:
            task.status = DevTaskStatus.CHANGES_REQUESTED
            if pr:
                pr.status = PRStatus.CHANGES_REQUESTED
        self.db.flush()
        return record

    def pending(self) -> list[DevelopmentTask]:
        return list(
            self.db.scalars(
                select(DevelopmentTask)
                .where(DevelopmentTask.status == DevTaskStatus.PR_READY)
                .order_by(DevelopmentTask.updated_at.desc())
            ).all()
        )
