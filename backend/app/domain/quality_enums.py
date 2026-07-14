"""Enumerations for the AI Review, Security & Quality Gate Engine (Sprint 14)."""

from enum import Enum


class FindingSeverity(str, Enum):
    """Severity of a review/security/performance finding (ordered)."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GateStatus(str, Enum):
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


class ComplianceStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ReadinessStatus(str, Enum):
    READY = "ready"
    NOT_READY = "not_ready"
    BLOCKED = "blocked"


class ReviewCategory(str, Enum):
    """Category of an architecture/code review finding."""

    LAYER_VIOLATION = "layer_violation"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    REPOSITORY_PATTERN = "repository_pattern"
    SERVICE_PATTERN = "service_pattern"
    API_CONSISTENCY = "api_consistency"
    NAMING = "naming"
    FOLDER_STRUCTURE = "folder_structure"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    DEAD_CODE = "dead_code"
    DUPLICATED_CODE = "duplicated_code"
    CODING_STANDARDS = "coding_standards"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"


class SecurityCategory(str, Enum):
    SECRET = "secret"
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    UNSAFE_DEPENDENCY = "unsafe_dependency"


class PerformanceCategory(str, Enum):
    SLOW_QUERY = "slow_query"
    LARGE_LOOP = "large_loop"
    MEMORY = "memory"
    API_PERFORMANCE = "api_performance"
    DATABASE_CALLS = "database_calls"
    CACHING = "caching"


class DependencyCategory(str, Enum):
    UNUSED = "unused"
    VERSION_CONFLICT = "version_conflict"
    DEPRECATED = "deprecated"
    LICENSE = "license"
    HEALTH = "health"


class DocumentationCategory(str, Enum):
    API_DOCS = "api_docs"
    KNOWLEDGE_BASE = "knowledge_base"
    ARCHITECTURE_DECISIONS = "architecture_decisions"
    TECHNICAL_DOCS = "technical_docs"
    MISSING_DOCS = "missing_docs"
