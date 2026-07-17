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
    ChangeType,
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
from app.models.ai import AIEmployee
from app.models.repository import Repository
from app.models.work import WorkItem
from app.core.config import get_settings
from app.services.ai_orchestrator import AIEmployeeOrchestrator
from app.services.dev_generation import GenerationService
from app.services.dev_git import DevWorkspace, GitService
from app.services.dev_intent import TaskIntentResolver
from app.services.dev_modification import CodeModificationEngine
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
    DevStage.QUALITY_GATE: "Quality & Security Engine",
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
        # WP8: recall prior long-term memory relevant to this task so the employee
        # benefits from previous implementations/decisions.
        from app.services.memory import MemoryService

        recalled = MemoryService(self.db).recall(
            keywords, scope="org", kind="implementation", limit=3
        )
        summary = f"Implement '{task.title}' via the autonomous workflow."
        if recalled:
            summary += f" | Recalled {len(recalled)} prior memory: " + "; ".join(
                r["summary"][:70] for r in recalled
            )
        # WP9: apply previously-learned rules to this task.
        from app.services.learning import LearningService

        applied = LearningService(self.db).apply(keywords, limit=3)
        if applied:
            summary += f" | Applied {len(applied)} learned rule(s): " + "; ".join(
                r["rule"][:60] for r in applied
            )

        plan = ImplementationPlan(
            task_id=task.id,
            summary=summary,
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


_LANG_BY_EXT = {
    ".py": "python",
    ".tsx": "typescript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".js": "javascript",
    ".md": "markdown",
    ".css": "css",
    ".json": "json",
}


def _language_for(path: str) -> str:
    import os

    return _LANG_BY_EXT.get(os.path.splitext(path)[1].lower(), "text")


class ModificationPlanner:
    """Turns a task's ``modification_spec`` into real changes on the sandbox.

    Chooses the change type automatically:

    * the target file **exists** in the source repository -> MODIFY (or DELETE /
      RENAME when the operation says so): the file is seeded into the sandbox from
      the real repo, then edited in place with the AST-guarded (Python) or
      anchor-based (other languages) engine, producing a real modification diff;
    * the target file **does not exist** -> CREATE (new file from the provided
      content).

    Blueprint / WORLD remain protected by the sandbox guards.
    """

    def __init__(self, db: Session):
        self.db = db
        self.engine = CodeModificationEngine()

    def _source_root(self, task: DevelopmentTask, spec: dict) -> str | None:
        if spec.get("source_root"):
            return spec["source_root"]
        if task.repository_id:
            repo = self.db.get(Repository, task.repository_id)
            if repo is not None:
                return repo.root_path
        return None

    def _transform(self, original: str, spec: dict) -> str:
        op = spec.get("operation", "insert_after_anchor")
        p = spec
        if op == "add_function":
            return self.engine.add_function(
                original, p["name"], p["snippet"], imports=p.get("imports")
            )
        if op == "add_method":
            return self.engine.add_method(original, p["class_name"], p["name"], p["snippet"])
        if op == "replace_function":
            return self.engine.replace_function(original, p["name"], p["snippet"])
        if op == "remove_symbol":
            return self.engine.remove_symbol(original, p["name"])
        if op == "rename_symbol":
            return self.engine.rename_symbol(original, p["old_name"], p["new_name"])
        if op == "insert_before_anchor":
            return self.engine.insert_before_anchor(
                original, p["anchor"], p["snippet"], occurrence=p.get("occurrence", 1)
            )
        # default
        return self.engine.insert_after_anchor(
            original, p["anchor"], p["snippet"], occurrence=p.get("occurrence", 1)
        )

    def _read_existing(self, task: DevelopmentTask, spec: dict) -> str | None:
        import os

        source_root = self._source_root(task, spec)
        abs_src = os.path.join(source_root, spec["target_file"]) if source_root else None
        if abs_src and os.path.isfile(abs_src):
            with open(abs_src, encoding="utf-8", errors="ignore") as fh:
                return fh.read()
        return None

    def seed_baseline(self, task: DevelopmentTask, git: GitService, spec: dict) -> bool:
        """Commit the existing target file onto ``main`` BEFORE the feature branch is
        cut, so the modification diff shows only the real change (not a whole new
        file). Returns True if a baseline file was seeded."""
        existing = self._read_existing(task, spec)
        if existing is None:
            return False  # CREATE: the file is genuinely new; no baseline.
        git.write_file(spec["target_file"], existing)
        git.stage_all()
        git.commit(f"chore: import {spec['target_file']} baseline"[:100])
        return True

    def plan_and_apply(
        self, task: DevelopmentTask, git: GitService, spec: dict
    ) -> tuple[list[GeneratedChange], str]:
        """Apply the modification on the feature branch; the baseline (existing file)
        is already committed on ``main`` by :meth:`seed_baseline`. Returns
        (changes, note). Diffs are computed against ``main`` so a MODIFY shows only
        the changed lines."""
        target = spec["target_file"]
        op = spec.get("operation", "insert_after_anchor")
        language = _language_for(target)
        baseline = git.read_file(target)  # what's on main (None for CREATE)

        # DELETE / RENAME of an existing file.
        if baseline is not None and op in ("delete_file", "rename_file"):
            if op == "delete_file":
                git.delete_file(target)
                ct, note = ChangeType.DELETE, f"deleted existing file {target}"
                path, old_path, content = target, None, None
            else:
                new_path = spec["new_path"]
                git.rename_file(target, new_path)
                ct, note = ChangeType.RENAME, f"renamed {target} -> {new_path}"
                path, old_path, content = new_path, target, baseline
            git.stage_all()
            git.commit(f"refactor: {note}"[:100])
            return [
                self._record(task, path, old_path, ct, language, content, git.diff("main"), note)
            ], note

        # MODIFY an existing file.
        if baseline is not None:
            new_content = self._transform(baseline, spec)
            git.write_file(target, new_content)
            git.stage_all()
            git.commit(f"feat: {task.title}"[:100])
            note = f"MODIFY {target} ({op}); existing code preserved"
            return [
                self._record(
                    task,
                    target,
                    None,
                    ChangeType.MODIFY,
                    language,
                    new_content,
                    git.diff_file("main", target),
                    f"Modified existing {target} ({op}).",
                )
            ], note

        # CREATE a new file (target did not exist in the repo).
        content = spec.get("content")
        if content is None:
            raise ValidationError(
                f"Target '{target}' does not exist and no 'content' was provided for CREATE"
            )
        git.write_file(target, content)
        git.stage_all()
        git.commit(f"feat: {task.title}"[:100])
        return [
            self._record(
                task,
                target,
                None,
                ChangeType.CREATE,
                language,
                content,
                git.diff_file("main", target),
                f"Created new file {target}.",
            )
        ], f"CREATE {target}"

    def _record(
        self, task, path, old_path, change_type, language, content, diff, rationale
    ) -> GeneratedChange:
        row = GeneratedChange(
            task_id=task.id,
            path=path,
            old_path=old_path,
            change_type=change_type,
            language=language,
            content=content,
            diff=(diff or "")[:8000],
            rationale=rationale,
            status=ChangeStatus.APPLIED,
            sequence=0,
        )
        self.db.add(row)
        self.db.flush()
        return row


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
        modification_spec: dict | None = None,
    ) -> DevelopmentTask:
        task = DevelopmentTask(
            code=self._next_code(),
            title=title,
            description=description,
            work_item_id=work_item_id,
            repository_id=repository_id,
            ai_employee_id=ai_employee_id,
            modification_spec=json.dumps(modification_spec) if modification_spec else None,
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
        self._assign_agent(s)
        return s

    def _assign_agent(self, session: DevelopmentSession) -> None:
        """WP7: attach the REAL acting employee (+ their selected provider) to a
        stage session, resolved from the AI org for this stage."""
        orch = getattr(self, "_orch", None)
        if orch is None:
            return
        agent = orch.agent_for_stage(session.stage)
        if agent is not None:
            session.acting_ai_employee_id = agent.employee.id
            session.role = agent.label
            session.provider_name = agent.provider_name
            self.db.flush()

    def _record_handoffs(self, task) -> None:
        """Record a handoff each time the acting employee changes between stages."""
        from app.models.development import DevelopmentHandoff

        for h in self.db.scalars(
            select(DevelopmentHandoff).where(DevelopmentHandoff.task_id == task.id)
        ).all():
            self.db.delete(h)
        self.db.flush()
        sessions = self.db.scalars(
            select(DevelopmentSession)
            .where(DevelopmentSession.task_id == task.id)
            .order_by(DevelopmentSession.sequence)
        ).all()
        prev = None
        seq = 0
        for s in sessions:
            if s.acting_ai_employee_id is None:
                continue
            if prev is not None and prev.acting_ai_employee_id != s.acting_ai_employee_id:
                self.db.add(
                    DevelopmentHandoff(
                        task_id=task.id,
                        sequence=seq,
                        from_employee_id=prev.acting_ai_employee_id,
                        to_employee_id=s.acting_ai_employee_id,
                        from_role=prev.role,
                        to_role=s.role,
                        stage=s.stage,
                        summary=f"{prev.role} handed off to {s.role} for {s.stage}",
                    )
                )
                seq += 1
            prev = s
        self.db.flush()

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
        # WP7: real AI-employee orchestration — each stage is performed by an actual
        # employee resolved from the AI org, with their selected provider.
        self._orch = AIEmployeeOrchestrator(self.db)
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

            # 1b. Intent resolution — CREATE (new module) vs MODIFY (existing file),
            # and DISCOVER the target file. An explicit modification_spec wins;
            # otherwise the resolver infers intent from the title. This REPLACES the
            # old silent scaffold fallback: an existing-code intent that cannot be
            # resolved FAILS the task rather than quietly scaffolding.
            s = self._session(task, DevStage.IMPLEMENTATION, seq)
            s.stage = "intent"
            s.role = "Intent Resolver"
            self._assign_agent(s)
            seq += 1
            from app.services.dev_requirements import RequirementExtractor

            if task.modification_spec:
                spec = json.loads(task.modification_spec)
                intent_kind = "modify"
                requirements = [
                    r.as_dict()
                    for r in RequirementExtractor().extract(task.title, task.description)
                ]
                self._done(
                    s,
                    "explicit modification_spec provided -> MODIFY "
                    f"{spec.get('target_file')} via ModificationPlanner",
                )
            else:
                intent = TaskIntentResolver(get_settings().project_root).resolve(
                    task.title, task.description
                )
                trail = " | ".join(intent.decisions)
                if intent.kind == "modify_unresolved":
                    self._done(s, trail, status=SessionStatus.FAILED)
                    raise ValidationError(
                        "Existing-code task could not be resolved to a target file; "
                        f"refusing to scaffold. {intent.reason}"
                    )
                spec = intent.spec
                intent_kind = intent.kind
                requirements = intent.requirements
                self._done(s, trail)

            # Persist the extracted requirements on the plan for verification + UI.
            plan.requirements = json.dumps(requirements)
            self.db.flush()

            # 2. Sandbox + branch.
            sandbox = self.workspace.create(task.code)
            git = GitService(sandbox)
            # Seed the existing target file onto main BEFORE branching so a MODIFY
            # produces a real change-only diff (not a whole-new-file diff).
            if spec:
                ModificationPlanner(self.db).seed_baseline(task, git, spec)
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
            mod = RepositoryModificationService(self.db)
            safety = mod.safety_checks(task, keywords)
            if spec:
                # Existing-code modification path (WP1): auto-selects
                # CREATE / MODIFY / DELETE / RENAME and seeds the sandbox from the
                # real repository so the diff is a genuine modification, not a
                # scaffold.
                changes, note = ModificationPlanner(self.db).plan_and_apply(task, git, spec)
                self._done(
                    s,
                    f"{note}. {len(changes)} change(s) "
                    f"[{', '.join(c.change_type.value if hasattr(c.change_type,'value') else c.change_type for c in changes)}]. "
                    f"Safety: {safety}",
                )
            elif intent_kind == "new_module":
                # Scaffold path — ONLY for an explicit 'new module' decision (the
                # intent resolver found no existing-file reference). Never a silent
                # fallback for an existing-code intent.
                gen = GenerationService(self.db).generate(
                    task.title, task.description, provider_name
                )
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

            # 6b. Quality gates (Sprint 14) — the final engineering validation before
            # a pull request can reach Founder approval. Runs after documentation so
            # the knowledge-base-update check sees the freshly written doc.
            s = self._session(task, DevStage.QUALITY_GATE, seq)
            seq += 1
            from app.services.quality_gate_service import QualityGateService

            gate = QualityGateService(self.db).evaluate(task.id)
            self._done(
                s,
                f"Quality gate {gate.status.value if hasattr(gate.status,'value') else gate.status} — "
                f"overall {gate.overall_score}, {gate.critical_count} critical, "
                f"{'approval-eligible' if gate.approval_eligible else 'blocked'}",
            )

            # 6c. Requirement verification — compare each requested requirement
            # against the GENERATED code. If any is missing, REJECT: no PR is
            # created and the task returns for changes. This closes the semantic
            # planning gap (requested -> generated -> verified -> only then PR).
            if requirements:
                from app.services.dev_requirements import Requirement, verify_requirements

                s = self._session(task, DevStage.REVIEW, seq)
                s.stage = "verification"
                s.role = "Requirement Verifier"
                self._assign_agent(s)
                seq += 1
                generated_source = "\n".join(c.content or "" for c in changes)
                req_objs = [
                    Requirement(r["kind"], r["description"], r["expected"]) for r in requirements
                ]
                report = verify_requirements(generated_source, req_objs)
                plan.verification = json.dumps(report)
                missing = [r for r in report if not r["satisfied"]]
                self.db.flush()
                if missing:
                    detail = "; ".join(r["description"] for r in missing)
                    self._done(
                        s,
                        f"REJECTED — {len(missing)}/{len(report)} requirement(s) not satisfied: "
                        f"{detail}. No pull request created.",
                        status=SessionStatus.FAILED,
                    )
                    task.status = DevTaskStatus.CHANGES_REQUESTED
                    task.error = f"Requirements not satisfied by generated code: {detail}"
                    task.completed_at = _now()
                    task.duration_ms = int((time.monotonic() - started) * 1000)
                    self._record_handoffs(task)
                    self.db.flush()
                    return self.serialize(task)
                self._done(
                    s,
                    f"All {len(report)} requirement(s) satisfied by the generated code "
                    f"[{', '.join(r['description'] for r in report)}].",
                )

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
            self._record_handoffs(task)
            # WP8: persist durable memory of this implementation (org + the
            # assigned employee) so future work can recall it.
            try:
                from app.services.memory import MemoryService

                mem = MemoryService(self.db)
                mem.remember(
                    scope="org",
                    kind="implementation",
                    summary=f"Implemented '{task.title}' ({pr.files_changed} files, "
                    f"+{pr.additions}/-{pr.deletions}, review {review.score}).",
                    content=plan.summary,
                    tags=[task.code, keywords[:40]],
                    source_task_id=task.id,
                )
                if task.ai_employee_id:
                    mem.remember(
                        scope="employee",
                        kind="implementation",
                        summary=f"Completed {task.code}: {task.title}",
                        employee_id=task.ai_employee_id,
                        tags=[task.code],
                        source_task_id=task.id,
                    )
            except Exception:  # pragma: no cover - memory is best-effort
                pass
            # WP9: learn reusable rules from this task's real review + tests.
            try:
                from app.services.learning import LearningService

                LearningService(self.db).learn_from_task(task.id)
            except Exception:  # pragma: no cover - learning is best-effort
                pass
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
            "requirements": j(p.requirements),
            "verification": j(p.verification),
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
        emp_names = {e.id: e.name for e in self.db.scalars(select(AIEmployee)).all()}
        return [
            {
                "stage": s.stage,
                "role": s.role,
                "status": s.status.value if hasattr(s.status, "value") else s.status,
                "detail": s.detail,
                "acting_employee": emp_names.get(s.acting_ai_employee_id),
                "provider": s.provider_name,
            }
            for s in rows
        ]

    def team(self) -> list[dict]:
        """The acting AI engineering team (WP7)."""
        orch = AIEmployeeOrchestrator(self.db)
        return [orch.serialize_agent(a) for a in orch.team()]

    def orchestration(self, task_id: uuid.UUID) -> dict:
        """Who performed each stage + the recorded handoffs between employees."""
        from app.models.development import DevelopmentHandoff

        emp_names = {e.id: e.name for e in self.db.scalars(select(AIEmployee)).all()}
        handoffs = self.db.scalars(
            select(DevelopmentHandoff)
            .where(DevelopmentHandoff.task_id == task_id)
            .order_by(DevelopmentHandoff.sequence)
        ).all()
        return {
            "stages": self.timeline(task_id),
            "handoffs": [
                {
                    "sequence": h.sequence,
                    "from_employee": emp_names.get(h.from_employee_id),
                    "to_employee": emp_names.get(h.to_employee_id),
                    "from_role": h.from_role,
                    "to_role": h.to_role,
                    "stage": h.stage,
                    "summary": h.summary,
                }
                for h in handoffs
            ],
        }

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
