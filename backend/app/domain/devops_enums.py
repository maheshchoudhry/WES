"""Enumerations for the Enterprise DevOps, CI/CD & Production Platform (Sprint 15)."""

from enum import Enum


class PipelineStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    AWAITING_PRODUCTION = "awaiting_production"
    CANCELLED = "cancelled"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class BuildStatus(str, Enum):
    PENDING = "pending"
    BUILDING = "building"
    SUCCESS = "success"
    FAILED = "failed"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    AWAITING_APPROVAL = "awaiting_approval"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DeployStrategy(str, Enum):
    STANDARD = "standard"
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"


class ReleaseStatus(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    RELEASED = "released"
    ROLLED_BACK = "rolled_back"


class ArtifactKind(str, Enum):
    TARBALL = "tarball"
    DOCKER_IMAGE = "docker_image"
    PACKAGE = "package"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class IncidentSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class RollbackStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
