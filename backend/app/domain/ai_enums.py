"""Enumerations for the AI Company Core (Sprint 06)."""

from enum import Enum


class AIRoleLevel(str, Enum):
    """Seniority level of an AI role."""

    EXECUTIVE = "executive"
    LEAD = "lead"
    OPERATIONAL = "operational"


class AIDecisionAuthority(str, Enum):
    """Decision authority an AI employee holds."""

    EXECUTIVE = "executive"
    LEAD = "lead"
    OPERATIONAL = "operational"


class AIEmployeeStatus(str, Enum):
    """Operational status of an AI employee."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
