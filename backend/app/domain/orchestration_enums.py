"""Enumerations for the AI Orchestration Engine (Sprint 09)."""

from enum import Enum


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ProviderHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ReviewOutcome(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"
    ESCALATED = "escalated"
