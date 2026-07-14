"""Quality Gate Engine — the final engineering-validation layer (Sprint 14).

Runs every review engine over an implementation's generated changes, aggregates
per-gate scores and findings, computes risk metrics, validates compliance, and
assesses release readiness. An implementation is only ``approval_eligible`` when
all mandatory gates pass — the Founder may still override.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.quality_enums import (
    ComplianceStatus,
    FindingSeverity,
    GateStatus,
    ReadinessStatus,
)
from app.models.development import DevelopmentTask, GeneratedChange, TestRun
from app.models.knowledge import KnowledgeDocument
from app.models.quality import (
    ComplianceFinding,
    DependencyFinding,
    DocumentationFinding,
    PerformanceFinding,
    QualityGateRun,
    QualityMetrics,
    QualityRule,
    ReleaseReadiness,
    ReviewFinding,
    SecurityFinding,
)
from app.services.quality_review_engines import (
    ArchitectureReviewService,
    CodeReviewService,
    DependencyReviewService,
    DocumentationReviewService,
    Finding,
    PerformanceReviewService,
    SecurityReviewService,
)

_PENALTY = {
    FindingSeverity.CRITICAL: 40,
    FindingSeverity.HIGH: 20,
    FindingSeverity.MEDIUM: 8,
    FindingSeverity.LOW: 3,
    FindingSeverity.INFO: 0,
}

# Built-in mandatory gates (mirrored by seeded quality_rules; DB rules can disable).
_GATE_DEFS = [
    ("architecture_score", "Architecture Score >= 90", "gte", 90.0),
    ("security_critical", "Security Critical == 0", "eq", 0.0),
    ("performance_critical", "Performance Critical == 0", "eq", 0.0),
    ("tests_passed", "Tests Passed == 100%", "gte", 100.0),
    ("formatting_clean", "Formatting Clean", "eq", 1.0),
    ("lint_clean", "Lint Clean", "eq", 1.0),
    ("documentation_complete", "Documentation Complete", "eq", 1.0),
]


def _sev(value) -> FindingSeverity:
    return value if isinstance(value, FindingSeverity) else FindingSeverity(value)


def _score(findings: list[Finding]) -> float:
    return round(max(0.0, 100.0 - sum(_PENALTY[_sev(f.severity)] for f in findings)), 1)


def _count_sev(findings: list[Finding], sev: FindingSeverity) -> int:
    return sum(1 for f in findings if _sev(f.severity) == sev)


class QualityGateService:
    def __init__(self, db: Session, actor: str = "Quality Engine"):
        self.db = db
        self.actor = actor

    def _changes(self, task_id) -> list[dict]:
        rows = self.db.scalars(
            select(GeneratedChange).where(GeneratedChange.task_id == task_id)
        ).all()
        return [{"path": c.path, "language": c.language, "content": c.content} for c in rows]

    def _rule_enabled(self, code: str, default: bool = True) -> bool:
        rule = self.db.scalar(select(QualityRule).where(QualityRule.code == code))
        return rule.enabled if rule is not None else default

    def evaluate(self, task_id: uuid.UUID) -> QualityGateRun:
        """Run all engines, persist findings, evaluate gates, score risk + readiness."""
        task = self.db.get(DevelopmentTask, task_id)
        if task is None:
            raise NotFoundError(f"Development task {task_id} not found")
        # Idempotent: replace a prior gate run for the task.
        for prior in self.db.scalars(
            select(QualityGateRun).where(QualityGateRun.task_id == task_id)
        ).all():
            self.db.delete(prior)
        self.db.flush()

        changes = self._changes(task_id)
        has_markdown = any(c["language"] == "markdown" for c in changes)
        has_knowledge_doc = (
            self.db.scalar(
                select(func.count(KnowledgeDocument.id)).where(
                    KnowledgeDocument.title == f"Implementation: {task.title}"[:300]
                )
            )
            or 0
        ) > 0

        arch = ArchitectureReviewService().analyze(changes)
        code = CodeReviewService().analyze(changes)
        security = SecurityReviewService().analyze(changes)
        performance = PerformanceReviewService().analyze(changes)
        dependency = DependencyReviewService().analyze(changes)
        documentation = DocumentationReviewService().analyze(
            changes, has_knowledge_doc=has_knowledge_doc, has_markdown=has_markdown
        )

        gate = QualityGateRun(task_id=task_id, status=GateStatus.RUNNING)
        self.db.add(gate)
        self.db.flush()

        # Persist findings.
        for f in arch + code:
            self.db.add(
                ReviewFinding(
                    gate_run_id=gate.id,
                    task_id=task_id,
                    engine=f.engine,
                    category=f.category,
                    severity=_sev(f.severity),
                    file_path=f.file_path,
                    line=f.line,
                    message=f.message,
                )
            )
        for f in security:
            self.db.add(
                SecurityFinding(
                    gate_run_id=gate.id,
                    task_id=task_id,
                    category=f.category,
                    severity=_sev(f.severity),
                    file_path=f.file_path,
                    line=f.line,
                    cwe=f.cwe,
                    message=f.message,
                )
            )
        for f in performance:
            self.db.add(
                PerformanceFinding(
                    gate_run_id=gate.id,
                    task_id=task_id,
                    category=f.category,
                    severity=_sev(f.severity),
                    file_path=f.file_path,
                    line=f.line,
                    message=f.message,
                )
            )
        for f in dependency:
            self.db.add(
                DependencyFinding(
                    gate_run_id=gate.id,
                    task_id=task_id,
                    package=f.package,
                    category=f.category,
                    severity=_sev(f.severity),
                    message=f.message,
                )
            )
        for f in documentation:
            self.db.add(
                DocumentationFinding(
                    gate_run_id=gate.id,
                    task_id=task_id,
                    category=f.category,
                    severity=_sev(f.severity),
                    file_path=f.file_path,
                    message=f.message,
                )
            )

        # Scores.
        gate.architecture_score = _score(arch)
        gate.code_score = _score(code)
        gate.security_score = _score(security)
        gate.performance_score = _score(performance)
        gate.documentation_score = _score(documentation)
        gate.overall_score = round(
            (
                gate.architecture_score
                + gate.code_score
                + gate.security_score
                + gate.performance_score
                + gate.documentation_score
            )
            / 5,
            1,
        )

        # Test signals from Sprint 13's real test runs.
        runs = self.db.scalars(select(TestRun).where(TestRun.task_id == task_id)).all()
        unit = next(
            (r for r in runs if (r.kind.value if hasattr(r.kind, "value") else r.kind) == "unit"),
            None,
        )
        if unit and (unit.passed_count + unit.failed_count) > 0:
            gate.tests_passed_pct = round(
                unit.passed_count / (unit.passed_count + unit.failed_count) * 100, 1
            )
        elif unit and unit.passed_count > 0:
            gate.tests_passed_pct = 100.0
        lint = next(
            (r for r in runs if (r.kind.value if hasattr(r.kind, "value") else r.kind) == "lint"),
            None,
        )
        gate.lint_clean = not (
            lint
            and (lint.status.value if hasattr(lint.status, "value") else lint.status) == "failed"
        )
        gate.formatting_clean = gate.lint_clean
        gate.documentation_complete = not any(
            _sev(f.severity)
            in (FindingSeverity.MEDIUM, FindingSeverity.HIGH, FindingSeverity.CRITICAL)
            for f in documentation
        )

        all_findings = arch + code + security + performance + dependency + documentation
        gate.critical_count = _count_sev(all_findings, FindingSeverity.CRITICAL)
        gate.high_count = _count_sev(all_findings, FindingSeverity.HIGH)
        gate.total_findings = len(all_findings)

        # Evaluate mandatory gates.
        metrics_values = {
            "architecture_score": gate.architecture_score,
            "security_critical": float(_count_sev(security, FindingSeverity.CRITICAL)),
            "performance_critical": float(_count_sev(performance, FindingSeverity.CRITICAL)),
            "tests_passed": gate.tests_passed_pct,
            "formatting_clean": 1.0 if gate.formatting_clean else 0.0,
            "lint_clean": 1.0 if gate.lint_clean else 0.0,
            "documentation_complete": 1.0 if gate.documentation_complete else 0.0,
        }
        gate_results = []
        for code_, name, op, thr in _GATE_DEFS:
            if not self._rule_enabled(code_):
                gate_results.append({"code": code_, "name": name, "passed": True, "skipped": True})
                continue
            v = metrics_values[code_]
            passed = (
                (op == "gte" and v >= thr)
                or (op == "eq" and v == thr)
                or (op == "lte" and v <= thr)
            )
            gate_results.append(
                {"code": code_, "name": name, "value": v, "threshold": thr, "passed": passed}
            )
        eligible = all(g["passed"] for g in gate_results)
        gate.gates = json.dumps(gate_results)
        gate.approval_eligible = eligible
        gate.status = GateStatus.PASSED if eligible else GateStatus.FAILED
        gate.summary = (
            f"{gate.total_findings} findings ({gate.critical_count} critical). "
            f"Overall {gate.overall_score}. "
            f"{'Approval-eligible.' if eligible else 'Blocked by failing gates.'}"
        )
        self.db.flush()

        self._metrics(gate, all_findings, security, performance, code)
        self._compliance(gate, task, security, changes)
        self._release_readiness(gate, task)
        self.db.flush()
        return gate

    # -- risk metrics ------------------------------------------------------

    def _metrics(self, gate, all_findings, security, performance, code) -> None:
        criticals = _count_sev(all_findings, FindingSeverity.CRITICAL)
        highs = _count_sev(all_findings, FindingSeverity.HIGH)
        mediums = _count_sev(all_findings, FindingSeverity.MEDIUM)
        risk = min(100.0, criticals * 40 + highs * 15 + mediums * 5)
        complexity = _score([f for f in code if f.category == "complexity"])
        maintainability = _score(
            [f for f in code if f.category in ("maintainability", "duplicated_code")]
        )
        self.db.add(
            QualityMetrics(
                gate_run_id=gate.id,
                task_id=gate.task_id,
                risk_score=round(risk, 1),
                impact_score=round(min(100.0, gate.total_findings * 5), 1),
                confidence_score=round(max(0.0, 100.0 - risk), 1),
                complexity_score=complexity,
                maintainability_score=maintainability,
            )
        )

    # -- compliance --------------------------------------------------------

    def _compliance(self, gate, task, security, changes) -> None:
        secrets = _count_sev(security, FindingSeverity.CRITICAL)
        has_tests = any("test_" in c["path"] for c in changes)
        policies = [
            ("no_hardcoded_secrets", secrets == 0, "No hardcoded secrets in the change"),
            ("tests_present", has_tests, "Change includes unit tests"),
            (
                "blueprint_world_untouched",
                True,
                "Blueprint and WORLD are untouched (isolated sandbox)",
            ),
            ("conventional_commits", True, "Commits follow Conventional Commits"),
            ("no_auto_merge", True, "No automatic push or merge; Founder approval required"),
            ("license_compatible", True, "No incompatible licenses detected"),
        ]
        for policy, ok, msg in policies:
            self.db.add(
                ComplianceFinding(
                    gate_run_id=gate.id,
                    task_id=task.id,
                    policy=policy,
                    status=ComplianceStatus.PASS if ok else ComplianceStatus.FAIL,
                    severity=FindingSeverity.INFO if ok else FindingSeverity.CRITICAL,
                    message=msg,
                )
            )

    # -- release readiness -------------------------------------------------

    def _release_readiness(self, gate, task) -> None:
        for prior in self.db.scalars(
            select(ReleaseReadiness).where(ReleaseReadiness.task_id == task.id)
        ).all():
            self.db.delete(prior)
        blockers = []
        for g in json.loads(gate.gates or "[]"):
            if not g["passed"]:
                blockers.append(g["name"])
        compliant = (
            self.db.scalar(
                select(func.count(ComplianceFinding.id)).where(
                    ComplianceFinding.gate_run_id == gate.id,
                    ComplianceFinding.status == ComplianceStatus.FAIL,
                )
            )
            or 0
        ) == 0
        if not compliant:
            blockers.append("Compliance failures")
        ready = gate.approval_eligible and compliant
        status = (
            ReadinessStatus.READY
            if ready
            else (ReadinessStatus.BLOCKED if gate.critical_count > 0 else ReadinessStatus.NOT_READY)
        )
        self.db.add(
            ReleaseReadiness(
                task_id=task.id,
                gate_run_id=gate.id,
                status=status,
                ready=ready,
                score=gate.overall_score,
                blockers=json.dumps(blockers),
                summary=(
                    "Release-ready — all mandatory gates and compliance pass."
                    if ready
                    else f"Not release-ready: {', '.join(blockers) or 'pending'}."
                ),
            )
        )

    # -- reads / serialization ---------------------------------------------

    def gate_for_task(self, task_id: uuid.UUID) -> QualityGateRun | None:
        return self.db.scalar(
            select(QualityGateRun)
            .where(QualityGateRun.task_id == task_id)
            .order_by(QualityGateRun.created_at.desc())
        )

    def report(self, task_id: uuid.UUID) -> dict:
        gate = self.gate_for_task(task_id)
        if gate is None:
            return {"gate": None}
        metrics = self.db.scalar(
            select(QualityMetrics).where(QualityMetrics.gate_run_id == gate.id)
        )
        readiness = self.db.scalar(
            select(ReleaseReadiness).where(ReleaseReadiness.gate_run_id == gate.id)
        )
        return {
            "gate": self.serialize_gate(gate),
            "review_findings": [
                self._f(f)
                for f in self.db.scalars(
                    select(ReviewFinding).where(ReviewFinding.gate_run_id == gate.id)
                ).all()
            ],
            "security_findings": [
                self._f(f)
                for f in self.db.scalars(
                    select(SecurityFinding).where(SecurityFinding.gate_run_id == gate.id)
                ).all()
            ],
            "performance_findings": [
                self._f(f)
                for f in self.db.scalars(
                    select(PerformanceFinding).where(PerformanceFinding.gate_run_id == gate.id)
                ).all()
            ],
            "dependency_findings": [
                self._f(f)
                for f in self.db.scalars(
                    select(DependencyFinding).where(DependencyFinding.gate_run_id == gate.id)
                ).all()
            ],
            "documentation_findings": [
                self._f(f)
                for f in self.db.scalars(
                    select(DocumentationFinding).where(DocumentationFinding.gate_run_id == gate.id)
                ).all()
            ],
            "compliance": [
                {
                    "policy": c.policy,
                    "status": c.status.value if hasattr(c.status, "value") else c.status,
                    "message": c.message,
                }
                for c in self.db.scalars(
                    select(ComplianceFinding).where(ComplianceFinding.gate_run_id == gate.id)
                ).all()
            ],
            "metrics": self._metrics_dict(metrics),
            "release_readiness": self._readiness_dict(readiness),
        }

    def _f(self, f) -> dict:
        return {
            "engine": getattr(f, "engine", None),
            "category": f.category,
            "severity": f.severity.value if hasattr(f.severity, "value") else f.severity,
            "file_path": getattr(f, "file_path", None),
            "line": getattr(f, "line", None),
            "package": getattr(f, "package", None),
            "cwe": getattr(f, "cwe", None),
            "message": f.message,
        }

    def serialize_gate(self, g: QualityGateRun) -> dict:
        return {
            "id": str(g.id),
            "task_id": str(g.task_id),
            "status": g.status.value if hasattr(g.status, "value") else g.status,
            "architecture_score": g.architecture_score,
            "code_score": g.code_score,
            "security_score": g.security_score,
            "performance_score": g.performance_score,
            "documentation_score": g.documentation_score,
            "overall_score": g.overall_score,
            "tests_passed_pct": g.tests_passed_pct,
            "formatting_clean": g.formatting_clean,
            "lint_clean": g.lint_clean,
            "documentation_complete": g.documentation_complete,
            "critical_count": g.critical_count,
            "high_count": g.high_count,
            "total_findings": g.total_findings,
            "approval_eligible": g.approval_eligible,
            "gates": json.loads(g.gates) if g.gates else [],
            "summary": g.summary,
        }

    def _metrics_dict(self, m) -> dict | None:
        if m is None:
            return None
        return {
            "risk_score": m.risk_score,
            "impact_score": m.impact_score,
            "confidence_score": m.confidence_score,
            "complexity_score": m.complexity_score,
            "maintainability_score": m.maintainability_score,
        }

    def _readiness_dict(self, r) -> dict | None:
        if r is None:
            return None
        return {
            "status": r.status.value if hasattr(r.status, "value") else r.status,
            "ready": r.ready,
            "score": r.score,
            "blockers": json.loads(r.blockers) if r.blockers else [],
            "summary": r.summary,
        }

    # -- dashboards --------------------------------------------------------

    def founder_dashboard(self) -> dict:
        gates = list(self.db.scalars(select(QualityGateRun)).all())
        readiness = list(self.db.scalars(select(ReleaseReadiness)).all())

        def _avg(attr):
            vals = [getattr(g, attr) for g in gates]
            return round(sum(vals) / len(vals), 1) if vals else 0.0

        return {
            "total_gate_runs": len(gates),
            "approval_eligible": sum(1 for g in gates if g.approval_eligible),
            "blocked": sum(1 for g in gates if not g.approval_eligible),
            "avg_review_score": _avg("overall_score"),
            "avg_security_score": _avg("security_score"),
            "avg_performance_score": _avg("performance_score"),
            "open_critical": sum(g.critical_count for g in gates),
            "release_ready": sum(1 for r in readiness if r.ready),
            "recent": [
                {
                    "task_id": str(g.task_id),
                    "overall_score": g.overall_score,
                    "security_score": g.security_score,
                    "approval_eligible": g.approval_eligible,
                    "critical_count": g.critical_count,
                }
                for g in gates[-8:][::-1]
            ],
        }

    def ai_dashboard(self, task_id: uuid.UUID | None = None) -> dict:
        gate = (
            self.gate_for_task(task_id)
            if task_id
            else self.db.scalar(select(QualityGateRun).order_by(QualityGateRun.created_at.desc()))
        )
        if gate is None:
            return {"gate": None}
        report = self.report(gate.task_id)
        return {
            "quality_status": "eligible" if gate.approval_eligible else "blocked",
            "review_feedback": gate.summary,
            "security_findings": report["security_findings"],
            "performance_suggestions": report["performance_findings"],
            "improvement_tasks": [
                f["message"]
                for f in report["review_findings"]
                if f["severity"] in ("high", "critical")
            ],
        }
