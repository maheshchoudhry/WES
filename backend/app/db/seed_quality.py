"""Seed the mandatory quality-gate rules (Sprint 14).

These mirror the built-in gate thresholds so the founder can see and (later) tune
them. Idempotent: skips when the rules already exist.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.quality_enums import FindingSeverity
from app.models.quality import QualityRule

# code, name, category, operator, threshold, severity
RULES = [
    (
        "architecture_score",
        "Architecture Score ≥ 90",
        "architecture",
        "gte",
        90.0,
        FindingSeverity.HIGH,
    ),
    ("security_critical", "Security Critical = 0", "security", "eq", 0.0, FindingSeverity.CRITICAL),
    (
        "performance_critical",
        "Performance Critical = 0",
        "performance",
        "eq",
        0.0,
        FindingSeverity.CRITICAL,
    ),
    ("tests_passed", "Tests Passed = 100%", "testing", "gte", 100.0, FindingSeverity.HIGH),
    ("formatting_clean", "Formatting Clean", "code", "eq", 1.0, FindingSeverity.MEDIUM),
    ("lint_clean", "Lint Clean", "code", "eq", 1.0, FindingSeverity.MEDIUM),
    (
        "documentation_complete",
        "Documentation Complete",
        "documentation",
        "eq",
        1.0,
        FindingSeverity.MEDIUM,
    ),
]


def seed_quality(db: Session) -> bool:
    """Seed the quality-gate rules. Idempotent."""
    if db.scalar(select(QualityRule).where(QualityRule.code == "architecture_score")):
        return False
    for code, name, category, operator, threshold, severity in RULES:
        db.add(
            QualityRule(
                code=code,
                name=name,
                category=category,
                operator=operator,
                threshold=threshold,
                severity=severity,
                enabled=True,
                mandatory=True,
                description=f"Mandatory gate: {name}.",
            )
        )
    db.flush()
    return True
