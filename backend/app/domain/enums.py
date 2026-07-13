"""Shared domain enumerations.

These encode the vocabulary of the WES organization as defined in the Company
directories (Employee-Directory / Department-Directory) and Blueprint Vol. 02–03.
"""

from enum import Enum


class EntityStatus(str, Enum):
    """Lifecycle status shared by Company, Department, and Employee."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class EmployeeStatus(str, Enum):
    """Employee lifecycle, extending the shared statuses with onboarding."""

    ONBOARDING = "onboarding"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AuthorityLevel(str, Enum):
    """Authority level of an employee (Blueprint Vol. 03 — Roles)."""

    EXECUTIVE = "executive"
    LEAD = "lead"
    OPERATIONAL = "operational"
