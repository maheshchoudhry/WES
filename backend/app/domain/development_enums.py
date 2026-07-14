"""Enumerations for the Autonomous Software Development Engine (Sprint 13)."""

from enum import Enum


class DevTaskStatus(str, Enum):
    """Lifecycle of an autonomous development task."""

    QUEUED = "queued"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    REVIEWING = "reviewing"
    DOCUMENTING = "documenting"
    PR_READY = "pr_ready"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    FAILED = "failed"
    COMPLETED = "completed"


class DevStage(str, Enum):
    """Stages of the implementation workflow (one session per stage)."""

    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    REPO_ANALYSIS = "repo_analysis"
    KNOWLEDGE = "knowledge"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    REVIEW = "review"
    QUALITY_GATE = "quality_gate"
    DOCUMENTATION = "documentation"
    GIT = "git"
    PULL_REQUEST = "pull_request"
    APPROVAL = "approval"


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ChangeType(str, Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class ChangeStatus(str, Enum):
    PROPOSED = "proposed"
    APPLIED = "applied"
    REVERTED = "reverted"


class ReviewDimension(str, Enum):
    ARCHITECTURE = "architecture"
    CODING_STANDARDS = "coding_standards"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    MAINTAINABILITY = "maintainability"
    TEST_COVERAGE = "test_coverage"


class ReviewSeverity(str, Enum):
    INFO = "info"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    BLOCKER = "blocker"


class ReviewOutcome(str, Enum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class TestKind(str, Enum):
    COMPILE = "compile"
    UNIT = "unit"
    INTEGRATION = "integration"
    LINT = "lint"
    TYPECHECK = "typecheck"
    FORMAT = "format"


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PRStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
