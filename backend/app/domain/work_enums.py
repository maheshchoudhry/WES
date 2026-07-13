"""Enumerations for the AI Work Management engine (Sprint 07)."""

from enum import Enum


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WorkStatus(str, Enum):
    BACKLOG = "backlog"
    PLANNED = "planned"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    ARCHIVED = "archived"


# Kanban columns (ordered; Blocked/Archived are off-board states).
KANBAN_COLUMNS = [
    WorkStatus.BACKLOG,
    WorkStatus.PLANNED,
    WorkStatus.ASSIGNED,
    WorkStatus.IN_PROGRESS,
    WorkStatus.REVIEW,
    WorkStatus.TESTING,
    WorkStatus.DONE,
]


class SprintStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"


class MilestoneStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DependencyType(str, Enum):
    BLOCKS = "blocks"
    RELATED = "related"
    DUPLICATE = "duplicate"


class AssignmentRole(str, Enum):
    ASSIGNEE = "assignee"
    REVIEWER = "reviewer"
