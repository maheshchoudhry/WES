"""Enumerations for the Repository Intelligence Engine (Sprint 12)."""

from enum import Enum


class Language(str, Enum):
    """Supported source/config languages."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    DOCKERFILE = "dockerfile"
    SQL = "sql"
    REQUIREMENTS = "requirements"
    TEXT = "text"
    OTHER = "other"


class SymbolType(str, Enum):
    """Kinds of code symbols extracted by the parser."""

    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    INTERFACE = "interface"
    ENUM = "enum"
    CONSTANT = "constant"
    VARIABLE = "variable"
    ROUTE = "route"
    MODEL = "model"
    SCHEMA = "schema"
    COMPONENT = "component"
    TYPE = "type"


class ModuleKind(str, Enum):
    PACKAGE = "package"
    MODULE = "module"
    DIRECTORY = "directory"


class ArchitectureLayer(str, Enum):
    """Detected architecture layers."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    API = "api"
    SERVICE = "service"
    MODEL = "model"
    SCHEMA = "schema"
    REPOSITORY = "repository"
    CONTROLLER = "controller"
    UTILITY = "utility"
    CONFIGURATION = "configuration"
    TEST = "test"
    DOCUMENTATION = "documentation"
    MIGRATION = "migration"
    OTHER = "other"


class DependencyType(str, Enum):
    IMPORT = "import"
    PACKAGE = "package"
    MODULE = "module"
    SERVICE = "service"
    DATABASE = "database"


class RelationshipType(str, Enum):
    IMPORTS = "imports"
    INHERITS = "inherits"
    CALLS = "calls"
    REFERENCES = "references"
    IMPLEMENTS = "implements"
    DEFINES = "defines"


class ScanStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
