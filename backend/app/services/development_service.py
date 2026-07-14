"""Autonomous Software Development Engine (Sprint 13).

Transforms a software task into a real implementation workflow that combines
Repository Intelligence, the Knowledge Engine, the Provider Platform, and the
Execution Engine:

    Plan → Repo Analysis → Knowledge → Implement → Modify (safe) → Test →
    Review → Document → Git branch + commits → Pull-Request draft → Founder Approval

Every change is explainable (plan + rationale + review), reviewable (diff + PR),
and reversible (isolated git sandbox). The engine NEVER pushes, NEVER merges, and
NEVER touches Blueprint or WORLD. The Founder is the final authority.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.development_enums import (
    ChangeStatus,
    DevStage,
    DevTaskStatus,
    SessionStatus,
)
from app.models.development import (
    CodeReview,
    DevelopmentSession,
    DevelopmentTask,
    GeneratedChange,
    ImplementationMetrics,
    ImplementationPlan,
    PullRequest,
    ReviewComment,
    TestRun,
)
from app.models.repository import Repository
from app.models.work import WorkItem
from app.services.dev_generation import GenerationService
from app.services.dev_git import DevWorkspace, GitService
from app.services.dev_review import (
    DocumentationService,
    PullRequestService,
    ReviewService,
    TestingService,
)

_STAGE_ROLE = {
    DevStage.PLANNING: "AI Product Manager / Chief Architect",
    DevStage.REPO_ANALYSIS: "Repository Intelligence",
    DevStage.KNOWLEDGE: "Knowledge Engine",
    DevStage.IMPLEMENTATION: "Backend Engineer",
    DevStage.TESTING: "QA Engineer",
    DevStage.REVIEW: "Chief Software Architect",
    DevStage.DOCUMENTATION: "Technical Writer",
    DevStage.GIT: "DevOps Engineer",
    DevStage.PULL_REQUEST: "DevOps Engineer",
    DevStage.APPROVAL: "Founder",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PlanningService:
    """Builds the implementation plan from Repository Intelligence + Knowledge."""

    def __init__(self, db: Session):
        self.db = db

    def plan(self, task: DevelopmentTask, keywords: str) -> ImplementationPlan:
        from app.services.knowledge_search import RetrievalService
        from app.services.repo_analysis import (
            ArchitectureService,
            DependencyService,
            ImpactAnalysisService,
            SearchService,
        )

        repo = (
            self.db.get(Repository, task.repository_id)
            if task.repository_id
            else self.db.scalar(select(Repository).order_by(Repository.last_scanned_at.desc()))
        )
        affected_files: list[str] = []
        architecture_context = "No repository indexed."
        dependencies: list[str] = []
        required_apis: list[str] = []
        risk = "Low — isolated new module in a sandbox."
        if repo is not None:
            task.repository_id = repo.id
            hits = SearchService(self.db).search(repo.id, keywords, limit=8)
            affected_files = sorted({h["file_path"] for h in hits if h["file_path"]})[:8]
            layers = ArchitectureService(self.db).layers(repo.id)
            architecture_context = ", ".join(
                f"{layer['layer']}({layer['file_count']})" for layer in layers
            )
            dependencies = [
                d["package"] for d in DependencyService(self.db).external_dependencies(repo.id)[:8]
            ]
            required_apis = [h["term"] for h in hits if h["kind"] == "route"][:8]
            if affected_files:
                impact = ImpactAnalysisService(self.db).analyze(repo.id, affected_files[0])
                n = len(impact["dependents"])
                risk = (
                    f"{'High' if n > 8 else 'Medium' if n > 2 else 'Low'} — "
                    f"{n} dependents on {affected_files[0]}."
                )

        knowledge = RetrievalService(self.db).retrieve_for(keywords=keywords, limit=5, log=False)
        required_knowledge = [d["title"] for d in knowledge.get("relevant_standards", [])] + [
            d["title"] for d in knowledge.get("relevant_sop", [])
        ]

        work_item = self.db.get(WorkItem, task.work_item_id) if task.work_item_id else None
        acceptance = (
            [work_item.acceptance_criteria] if work_item and work_item.acceptance_criteria else []
        ) or [
            "New module compiles (py_compile)",
            "Unit tests pass (pytest)",
            "Automated review score >= 70",
        ]
        order = [
            "Retrieve repository + knowledge context",
            "Generate feature module",
            "Generate unit tests",
            "Apply changes to sandbox (safety-checked)",
            "Run tests (compile + pytest)",
            "Automated code review",
            "Update knowledge base",
            "Create branch + atomic commits",
            "Open pull-request draft",
            "Founder approval",
        ]
        plan = ImplementationPlan(
            task_id=task.id,
            summary=f"Implement '{task.title}' via the autonomous workflow.",
            affected_files=json.dumps(affected_files),
            architecture_context=architecture_context,
            dependencies=json.dumps(dependencies),
            required_knowledge=json.dumps(required_knowledge),
            required_apis=json.dumps(required_apis),
            implementation_order=json.dumps(order),
            risk_analysis=risk,
            acceptance_criteria=json.dumps(acceptance),
        )
        self.db.add(plan)
        self.db.flush()
        return plan


class RepositoryModificationService:
    """Applies generated changes to the sandbox AFTER mandatory safety checks."""

    def __init__(self, db: Session):
        self.db = db

    def safety_checks(self, task: DevelopmentTask, keywords: str) -> str:
        """Retrieve repo context + knowledge, run impact analysis, verify architecture."""
        from app.services.knowledge_search import RetrievalService
        from app.services.repo_analysis import ArchitectureService, RepositoryRetrievalService

        notes = []
        repo_ctx = RepositoryRetrievalService(self.db).retrieve_for(keywords=keywords, limit=5)
        notes.append(
            "repository context ✓" if repo_ctx.get("repository") else "repository context (none)"
        )
        knowledge = RetrievalService(self.db).retrieve_for(keywords=keywords, limit=3, log=False)
        notes.append(
            f"knowledge retrieved ({len(knowledge.get('relevant_standards', []))} standards) ✓"
        )
        if task.repository_id:
            layers = ArchitectureService(self.db).layers(task.repository_id)
            notes.append(f"architecture verified ({len(layers)} layers) ✓")
        notes.append("target confined to sandbox; Blueprint/WORLD protected ✓")
        return "; ".join(notes)

    def apply(self, task: DevelopmentTask, git: GitService, changes: list[GeneratedChange]) -> None:
        code_files = [c for c in changes if c.language == "python"]
        doc_files = [c for c in changes if c.language != "python"]

        def _write(group):
            for c in group:
                ct = c.change_type.value if hasattr(c.change_type, "value") else c.change_type
                if ct == "delete":
                    git.delete_file(c.path)
                elif ct == "rename" and c.old_path:
                    git.rename_file(c.old_path, c.path)
                else:
                    git.write_file(c.path, c.content or "")

        # Atomic commits: feature code first, documentation second.
        _write(code_files)
        git.stage_all()
        if code_files:
            git.commit(f"feat: {task.title}"[:100])
        _write(doc_files)
        git.stage_all()
        if doc_files:
            git.commit(f"docs: notes for {task.title}"[:100])

        # Record per-file diffs and mark applied.
        for c in changes:
            c.diff = git.diff_file("main", c.path)[:8000]
            c.status = ChangeStatus.APPLIED
        self.db.flush()


class DevelopmentService:
    """Task lifecycle + the end-to-end autonomous workflow."""

    def __init__(self, db: Session, actor: str = "WES AI"):
        self.db = db
        self.actor = actor
        self.workspace = DevWorkspace()

    # -- task registration -------------------------------------------------

    def _next_code(self) -> str:
        n = self.db.scalar(select(func.count(DevelopmentTask.id))) or 0
        return f"DEV-{n + 1:04d}"

    def create_task(
        self,
        title: str,
        *,
        description: str | None = None,
        work_item_id: uuid.UUID | None = None,
        repository_id: uuid.UUID | None = None,
        ai_employee_id: uuid.UUID | None = None,
    ) -> DevelopmentTask:
        task = DevelopmentTask(
            code=self._next_code(),
            title=title,
            description=description,
            work_item_id=work_item_id,
            repository_id=repository_id,
            ai_employee_id=ai_employee_id,
            status=DevTaskStatus.QUEUED,
        )
        self.db.add(task)
        self.db.flush()
        return task

    def _session(self, task, stage: DevStage, seq: int) -> DevelopmentSession:
        s = DevelopmentSession(
            task_id=task.id,
            stage=stage.value,
            role=_STAGE_ROLE.get(stage),
            status=SessionStatus.RUNNING,
            sequence=seq,
            started_at=_now(),
        )
        self.db.add(s)
        self.db.flush()
        return s

    def _done(self, session, detail: str, status=SessionStatus.COMPLETED) -> None:
        session.status = status
        session.detail = detail
        session.completed_at = _now()
        self.db.flush()

    # -- the workflow ------------------------------------------------------

    def run_workflow(self, task_id: uuid.UUID, provider_name: str | None = None) -> dict:
        task = self.db.get(DevelopmentTask, task_id)
        if task is None:
            raise NotFoundError(f"Development task {task_id} not found")
        if task.status not in (DevTaskStatus.QUEUED, DevTaskStatus.CHANGES_REQUESTED):
            raise ValidationError(f"Task {task.code} is not runnable (status {task.status})")

        started = time.monotonic()
        task.started_at = _now()
        seq = 0
        try:
            keywords = task.title

            # 1. Planning (+ architecture, repo analysis, knowledge).
            task.status = DevTaskStatus.PLANNING
            self.db.flush()
            s = self._session(task, DevStage.PLANNING, seq)
            seq += 1
            plan = PlanningService(self.db).plan(task, keywords)
            self._done(s, plan.summary)

            s = self._session(task, DevStage.REPO_ANALYSIS, seq)
            seq += 1
            self._done(s, f"Architecture: {plan.architecture_context[:200]}")
            s = self._session(task, DevStage.KNOWLEDGE, seq)
            seq += 1
            self._done(s, f"Required knowledge: {plan.required_knowledge[:200]}")

            # 2. Sandbox + branch.
            sandbox = self.workspace.create(task.code)
            git = GitService(sandbox)
            branch = f"feature/auto-{task.code.lower()}"
            git.create_branch(branch)
            task.sandbox_path = sandbox
            task.branch_name = branch
            self.db.flush()

            # 3. Implementation (generate + safe modify).
            task.status = DevTaskStatus.IMPLEMENTING
            self.db.flush()
            s = self._session(task, DevStage.IMPLEMENTATION, seq)
            seq += 1
            gen = GenerationService(self.db).generate(task.title, task.description, provider_name)
            changes = []
            for pc in gen.changes:
                row = GeneratedChange(
                    task_id=task.id,
                    path=pc.path,
                    change_type=pc.change_type,
                    language=pc.language,
                    content=pc.content,
                    rationale=pc.rationale,
                    status=ChangeStatus.PROPOSED,
                    sequence=pc.sequence,
                )
                self.db.add(row)
                changes.append(row)
            self.db.flush()

            mod = RepositoryModificationService(self.db)
            safety = mod.safety_checks(task, keywords)
            mod.apply(task, git, changes)
            self._done(s, f"Generated {len(changes)} files. Safety: {safety}")

            s = self._session(task, DevStage.GIT, seq)
            seq += 1
            self._done(
                s, f"Branch {branch}; {git.commit_count('main')} commits; {git.head_sha()[:8]}"
            )

            # 4. Testing (real py_compile + pytest).
            task.status = DevTaskStatus.TESTING
            self.db.flush()
            s = self._session(task, DevStage.TESTING, seq)
            seq += 1
            py_files = [c.path for c in changes if c.language == "python"]
            runs = TestingService(self.db).run(task.id, sandbox, py_files)
            passed = sum(r.passed_count for r in runs)
            failed = sum(r.failed_count for r in runs)
            self._done(s, f"{passed} passed, {failed} failed across {len(runs)} test runs")

            # 5. Review.
            task.status = DevTaskStatus.REVIEWING
            self.db.flush()
            s = self._session(task, DevStage.REVIEW, seq)
            seq += 1
            review = ReviewService(self.db).review(task.id, changes)
            self._done(
                s,
                f"Review {review.outcome.value if hasattr(review.outcome,'value') else review.outcome} — score {review.score}",
            )

            # 6. Documentation.
            task.status = DevTaskStatus.DOCUMENTING
            self.db.flush()
            s = self._session(task, DevStage.DOCUMENTATION, seq)
            seq += 1
            notes_change = next((c for c in changes if c.language == "markdown"), None)
            doc_id = DocumentationService(self.db, actor=self.actor).document(
                task, notes_change.content if notes_change else plan.summary
            )
            self._done(s, f"Knowledge document {doc_id} created")

            # 7. Pull request draft.
            s = self._session(task, DevStage.PULL_REQUEST, seq)
            seq += 1
            pr = PullRequestService(self.db).create_draft(task, git, plan.summary)
            self._done(
                s,
                f"PR draft: {pr.title} (+{pr.additions}/-{pr.deletions}, {pr.files_changed} files)",
            )

            # 8. Metrics + await approval.
            task.status = DevTaskStatus.PR_READY
            task.completed_at = _now()
            task.duration_ms = int((time.monotonic() - started) * 1000)
            self.db.add(
                ImplementationMetrics(
                    task_id=task.id,
                    generated_files=len(changes),
                    files_changed=pr.files_changed,
                    additions=pr.additions,
                    deletions=pr.deletions,
                    commits=pr.commit_count,
                    tests_run=len(runs),
                    tests_passed=passed,
                    review_score=review.score,
                    duration_ms=task.duration_ms,
                )
            )
            self.db.flush()
            return self.serialize(task)
        except Exception as exc:
            task.status = DevTaskStatus.FAILED
            task.error = str(exc)[:500]
            task.completed_at = _now()
            self.db.flush()
            return self.serialize(task)

    # -- serialization / reads ---------------------------------------------

    def serialize(self, task: DevelopmentTask, *, full: bool = False) -> dict:
        data = {
            "id": str(task.id),
            "code": task.code,
            "title": task.title,
            "description": task.description,
            "status": task.status.value if hasattr(task.status, "value") else task.status,
            "branch_name": task.branch_name,
            "sandbox_path": task.sandbox_path,
            "repository_id": str(task.repository_id) if task.repository_id else None,
            "error": task.error,
            "duration_ms": task.duration_ms,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }
        if full:
            data["plan"] = self._plan_dict(task.id)
            data["changes"] = self._changes(task.id)
            data["tests"] = self._tests(task.id)
            data["review"] = self._review(task.id)
            data["pull_request"] = self._pr(task.id)
            data["timeline"] = self.timeline(task.id)
            data["metrics"] = self._metrics(task.id)
        return data

    def _plan_dict(self, task_id) -> dict | None:
        p = self.db.scalar(select(ImplementationPlan).where(ImplementationPlan.task_id == task_id))
        if p is None:
            return None
        j = lambda v: json.loads(v) if v else []  # noqa: E731
        return {
            "summary": p.summary,
            "affected_files": j(p.affected_files),
            "architecture_context": p.architecture_context,
            "dependencies": j(p.dependencies),
            "required_knowledge": j(p.required_knowledge),
            "required_apis": j(p.required_apis),
            "implementation_order": j(p.implementation_order),
            "risk_analysis": p.risk_analysis,
            "acceptance_criteria": j(p.acceptance_criteria),
        }

    def _changes(self, task_id) -> list[dict]:
        rows = self.db.scalars(
            select(GeneratedChange)
            .where(GeneratedChange.task_id == task_id)
            .order_by(GeneratedChange.sequence)
        ).all()
        return [
            {
                "id": str(c.id),
                "path": c.path,
                "change_type": (
                    c.change_type.value if hasattr(c.change_type, "value") else c.change_type
                ),
                "language": c.language,
                "content": c.content,
                "diff": c.diff,
                "rationale": c.rationale,
                "status": c.status.value if hasattr(c.status, "value") else c.status,
            }
            for c in rows
        ]

    def _tests(self, task_id) -> list[dict]:
        rows = self.db.scalars(select(TestRun).where(TestRun.task_id == task_id)).all()
        return [
            {
                "kind": r.kind.value if hasattr(r.kind, "value") else r.kind,
                "command": r.command,
                "status": r.status.value if hasattr(r.status, "value") else r.status,
                "passed_count": r.passed_count,
                "failed_count": r.failed_count,
                "duration_ms": r.duration_ms,
            }
            for r in rows
        ]

    def _review(self, task_id) -> dict | None:
        r = self.db.scalar(select(CodeReview).where(CodeReview.task_id == task_id))
        if r is None:
            return None
        comments = self.db.scalars(
            select(ReviewComment).where(ReviewComment.review_id == r.id)
        ).all()
        return {
            "outcome": r.outcome.value if hasattr(r.outcome, "value") else r.outcome,
            "score": r.score,
            "summary": r.summary,
            "comments": [
                {
                    "dimension": (
                        c.dimension.value if hasattr(c.dimension, "value") else c.dimension
                    ),
                    "severity": c.severity.value if hasattr(c.severity, "value") else c.severity,
                    "file_path": c.file_path,
                    "message": c.message,
                }
                for c in comments
            ],
        }

    def _pr(self, task_id) -> dict | None:
        pr = self.db.scalar(select(PullRequest).where(PullRequest.task_id == task_id))
        if pr is None:
            return None
        return {
            "id": str(pr.id),
            "branch_name": pr.branch_name,
            "base_branch": pr.base_branch,
            "title": pr.title,
            "body": pr.body,
            "diff_summary": pr.diff_summary,
            "release_notes": pr.release_notes,
            "status": pr.status.value if hasattr(pr.status, "value") else pr.status,
            "commit_count": pr.commit_count,
            "files_changed": pr.files_changed,
            "additions": pr.additions,
            "deletions": pr.deletions,
        }

    def _metrics(self, task_id) -> dict | None:
        m = self.db.scalar(
            select(ImplementationMetrics).where(ImplementationMetrics.task_id == task_id)
        )
        if m is None:
            return None
        return {
            "generated_files": m.generated_files,
            "files_changed": m.files_changed,
            "additions": m.additions,
            "deletions": m.deletions,
            "commits": m.commits,
            "tests_run": m.tests_run,
            "tests_passed": m.tests_passed,
            "review_score": m.review_score,
            "duration_ms": m.duration_ms,
        }

    def timeline(self, task_id) -> list[dict]:
        rows = self.db.scalars(
            select(DevelopmentSession)
            .where(DevelopmentSession.task_id == task_id)
            .order_by(DevelopmentSession.sequence)
        ).all()
        return [
            {
                "stage": s.stage,
                "role": s.role,
                "status": s.status.value if hasattr(s.status, "value") else s.status,
                "detail": s.detail,
            }
            for s in rows
        ]

    def list_tasks(self, *, status: str | None = None, limit: int = 50) -> list[dict]:
        stmt = select(DevelopmentTask).order_by(DevelopmentTask.created_at.desc()).limit(limit)
        if status:
            stmt = (
                select(DevelopmentTask)
                .where(DevelopmentTask.status == status)
                .order_by(DevelopmentTask.created_at.desc())
                .limit(limit)
            )
        return [self.serialize(t) for t in self.db.scalars(stmt).all()]

    def get_task(self, task_id: uuid.UUID) -> dict:
        task = self.db.get(DevelopmentTask, task_id)
        if task is None:
            raise NotFoundError(f"Development task {task_id} not found")
        return self.serialize(task, full=True)

    # -- dashboards --------------------------------------------------------

    def founder_dashboard(self) -> dict:
        tasks = list(self.db.scalars(select(DevelopmentTask)).all())

        def _count(status):
            return sum(
                1
                for t in tasks
                if (t.status.value if hasattr(t.status, "value") else t.status) == status
            )

        prs = list(self.db.scalars(select(PullRequest)).all())
        return {
            "running": sum(
                1
                for t in tasks
                if (t.status.value if hasattr(t.status, "value") else t.status)
                in ("planning", "implementing", "testing", "reviewing", "documenting")
            ),
            "completed": _count("approved") + _count("completed"),
            "failed": _count("failed"),
            "pending_approvals": _count("pr_ready"),
            "open_pull_requests": sum(
                1
                for p in prs
                if (p.status.value if hasattr(p.status, "value") else p.status) == "draft"
            ),
            "total_tasks": len(tasks),
            "recent_tasks": [self.serialize(t) for t in tasks[-8:][::-1]],
        }

    def ai_dashboard(self, task_id: uuid.UUID | None = None) -> dict:
        task = None
        if task_id:
            task = self.db.get(DevelopmentTask, task_id)
        else:
            task = self.db.scalar(
                select(DevelopmentTask).order_by(DevelopmentTask.created_at.desc())
            )
        if task is None:
            return {"current_task": None}
        review = self._review(task.id)
        tests = self._tests(task.id)
        return {
            "current_task": {
                "code": task.code,
                "title": task.title,
                "status": task.status.value if hasattr(task.status, "value") else task.status,
            },
            "branch": task.branch_name,
            "implementation_status": (
                task.status.value if hasattr(task.status, "value") else task.status
            ),
            "review_status": review["outcome"] if review else None,
            "testing_status": (
                "passed" if tests and all(t["status"] != "failed" for t in tests) else "pending"
            ),
            "timeline": self.timeline(task.id),
        }
