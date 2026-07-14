"""Enumerations for the AI Execution Engine (Sprint 08)."""

from enum import Enum


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class HandoffStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    COMPLETED = "completed"


class PromptType(str, Enum):
    SYSTEM = "system"
    ROLE = "role"
    TASK = "task"
    REVIEW = "review"
    ESCALATION = "escalation"


class SOPCategory(str, Enum):
    CODING = "coding"
    REVIEW = "review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DOCUMENTATION = "documentation"
    SECURITY = "security"


class DecisionRuleType(str, Enum):
    APPROVAL = "approval"
    ESCALATION = "escalation"
    REVIEW = "review"
    AUTHORITY_LIMIT = "authority_limit"
