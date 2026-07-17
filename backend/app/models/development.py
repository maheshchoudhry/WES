"""Autonomous Software Development Engine ORM models (Sprint 13).

Models a software task's autonomous implementation: the task, its per-stage
sessions, the implementation plan, generated changes, code reviews and comments,
test runs, a pull-request draft, approval history, and implementation metrics.
Every change is explainable, reviewable, and reversible — and the Founder is the
final authority (no auto-merge, no auto-push).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.development_enums import (
    ApprovalDecision,
    ChangeStatus,
    ChangeType,
    DevTaskStatus,
    PRStatus,
    ReviewDimension,
    ReviewOutcome,
    ReviewSeverity,
    SessionStatus,
    TestKind,
    TestStatus,
)
from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class DevelopmentTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "development_tasks"

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DevTaskStatus] = mapped_column(
        String(30), nullable=False, default=DevTaskStatus.QUEUED, index=True
    )
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True
    )
    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True
    )
    ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    sandbox_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    branch_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Optional existing-code modification intent (JSON): target_file, operation,
    # anchor/snippet/symbol/new_name, source_root. Absent => scaffold a new module.
    modification_spec: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DevelopmentSession(UUIDPrimaryKeyMixin, Base):
    """One row per workflow stage — the task timeline."""

    __tablename__ = "development_sessions"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(String(30), nullable=False)
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # WP7: the REAL AI employee that performed this stage + the provider selected
    # for them (mock until a live provider is configured).
    acting_ai_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    provider_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        String(20), nullable=False, default=SessionStatus.PENDING
    )
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ImplementationPlan(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "implementation_plans"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_files: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    architecture_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    dependencies: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    required_knowledge: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    required_apis: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    implementation_order: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    risk_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    # Concrete, individually-verifiable requirements extracted from the task, and
    # the verification report produced before the PR gate (both JSON).
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    verification: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class GeneratedChange(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "generated_changes"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    old_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    change_type: Mapped[ChangeType] = mapped_column(String(20), nullable=False)
    language: Mapped[str | None] = mapped_column(String(40), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ChangeStatus] = mapped_column(
        String(20), nullable=False, default=ChangeStatus.PROPOSED
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CodeReview(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "code_reviews"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    outcome: Mapped[ReviewOutcome] = mapped_column(String(30), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReviewComment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "review_comments"

    review_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("code_reviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dimension: Mapped[ReviewDimension] = mapped_column(String(30), nullable=False)
    severity: Mapped[ReviewSeverity] = mapped_column(
        String(20), nullable=False, default=ReviewSeverity.INFO
    )
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class TestRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "test_runs"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[TestKind] = mapped_column(String(20), nullable=False)
    command: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[TestStatus] = mapped_column(String(20), nullable=False)
    passed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PullRequest(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "pull_requests"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_name: Mapped[str] = mapped_column(String(200), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(200), nullable=False, default="main")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PRStatus] = mapped_column(String(20), nullable=False, default=PRStatus.DRAFT)
    commit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    additions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deletions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ApprovalHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "approval_history"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pull_request_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("pull_requests.id", ondelete="SET NULL"), nullable=True
    )
    decision: Mapped[ApprovalDecision] = mapped_column(String(30), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ImplementationMetrics(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "implementation_metrics"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generated_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    additions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deletions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tests_run: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tests_passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    review_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DevelopmentHandoff(UUIDPrimaryKeyMixin, Base):
    """A recorded handoff of work between two AI employees (WP7)."""

    __tablename__ = "development_handoffs"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("development_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    from_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    to_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("ai_employees.id", ondelete="SET NULL"), nullable=True
    )
    from_role: Mapped[str | None] = mapped_column(String(160), nullable=True)
    to_role: Mapped[str | None] = mapped_column(String(160), nullable=True)
    stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
