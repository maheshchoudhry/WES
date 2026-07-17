"""Self-learning (WP9).

Completed work improves future work. After a task finishes, the company derives
reusable rules from REAL evidence — code-review comments, quality findings, and
the test/verification outcome — and reinforces them (``occurrences``) when the
same lesson recurs. Future tasks recall the active rules and their
``applied_count`` grows, closing the learn → apply loop. Deterministic today; a
live provider (WP2) can later synthesise richer rules through the same records.
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.development import (
    CodeReview,
    DevelopmentTask,
    GeneratedChange,
    ReviewComment,
    TestRun,
)
from app.models.learning import LearningRule

_STOP = {"a", "an", "the", "to", "on", "for", "of", "and", "add", "new", "with", "in"}

# review dimension -> learning-rule kind.
_DIM_KIND = {
    "security": "bug_prevention",
    "performance": "bug_prevention",
    "architecture": "architecture",
    "documentation": "coding_standard",
    "coding_standards": "coding_standard",
    "maintainability": "coding_standard",
    "test_coverage": "coding_standard",
}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in _STOP and len(t) > 2}


class LearningService:
    def __init__(self, db: Session):
        self.db = db

    def _upsert(
        self,
        *,
        kind: str,
        rule: str,
        dimension: str | None = None,
        evidence: str | None = None,
        source_task_id: uuid.UUID | None = None,
    ) -> LearningRule:
        rule = rule[:500]
        existing = self.db.scalar(select(LearningRule).where(LearningRule.rule == rule))
        if existing is not None:
            existing.occurrences += 1
            self.db.flush()
            return existing
        row = LearningRule(
            kind=kind,
            rule=rule,
            dimension=dimension,
            evidence=evidence,
            source_task_id=source_task_id,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def learn_from_task(self, task_id: uuid.UUID) -> list[LearningRule]:
        """Derive/reinforce rules from a finished task's real review + tests."""
        task = self.db.get(DevelopmentTask, task_id)
        if task is None:
            return []
        learned: list[LearningRule] = []

        # 1. Rules from actual code-review comments.
        review = self.db.scalar(select(CodeReview).where(CodeReview.task_id == task_id))
        if review is not None:
            comments = self.db.scalars(
                select(ReviewComment).where(ReviewComment.review_id == review.id)
            ).all()
            for c in comments:
                dim = c.dimension.value if hasattr(c.dimension, "value") else c.dimension
                learned.append(
                    self._upsert(
                        kind=_DIM_KIND.get(dim, "coding_standard"),
                        rule=c.message,
                        dimension=dim,
                        evidence=f"review of {task.code}",
                        source_task_id=task_id,
                    )
                )

        # 2. Reinforcement rule from the real test/verification outcome, per
        # primary language of the change set.
        langs = {
            c.language
            for c in self.db.scalars(
                select(GeneratedChange).where(GeneratedChange.task_id == task_id)
            ).all()
            if c.language
        }
        runs = self.db.scalars(select(TestRun).where(TestRun.task_id == task_id)).all()
        passed = sum(r.passed_count for r in runs)
        for lang in langs or {"code"}:
            learned.append(
                self._upsert(
                    kind="coding_standard",
                    rule=f"{lang} changes must compile and pass tests before a PR",
                    dimension="test_coverage",
                    evidence=f"{task.code}: {passed} tests passed",
                    source_task_id=task_id,
                )
            )
        return learned

    def apply(self, keywords: str, *, limit: int = 5) -> list[dict]:
        """Recall active rules relevant to a task and count the application."""
        rows = self.db.scalars(
            select(LearningRule)
            .where(LearningRule.active.is_(True))
            .order_by(LearningRule.occurrences.desc())
            .limit(100)
        ).all()
        qk = _tokens(keywords)
        ranked = sorted(
            rows,
            key=lambda r: len(qk & _tokens(r.rule)) + r.occurrences * 0.01,
            reverse=True,
        )[:limit]
        for r in ranked:
            r.applied_count += 1
        self.db.flush()
        return [self.serialize(r) for r in ranked]

    def rules(self, *, kind: str | None = None, limit: int = 100) -> list[dict]:
        stmt = select(LearningRule).order_by(LearningRule.occurrences.desc()).limit(limit)
        if kind:
            stmt = (
                select(LearningRule)
                .where(LearningRule.kind == kind)
                .order_by(LearningRule.occurrences.desc())
                .limit(limit)
            )
        return [self.serialize(r) for r in self.db.scalars(stmt).all()]

    def summary(self) -> dict:
        total = self.db.scalar(select(func.count(LearningRule.id))) or 0
        applied = self.db.scalar(select(func.sum(LearningRule.applied_count))) or 0
        by_kind = {}
        for r in self.db.scalars(select(LearningRule)).all():
            by_kind[r.kind] = by_kind.get(r.kind, 0) + 1
        return {"total_rules": total, "total_applications": int(applied), "by_kind": by_kind}

    @staticmethod
    def serialize(r: LearningRule) -> dict:
        return {
            "id": str(r.id),
            "kind": r.kind,
            "rule": r.rule,
            "dimension": r.dimension,
            "occurrences": r.occurrences,
            "applied_count": r.applied_count,
            "evidence": r.evidence,
            "active": r.active,
        }
