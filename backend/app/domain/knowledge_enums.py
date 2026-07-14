"""Enumerations for the Organizational Knowledge Engine (Sprint 10).

Document types, lifecycle status, review decisions, relationship types, and the
entity types the knowledge graph can point at. Categories are seeded data (a
table), not an enum, so the taxonomy can grow without a migration.
"""

from enum import Enum


class DocumentType(str, Enum):
    """Kind of knowledge document."""

    ARCHITECTURE = "architecture"
    ADR = "adr"
    SOP = "sop"
    SPECIFICATION = "specification"
    API = "api"
    DESIGN = "design"
    MEETING_NOTES = "meeting_notes"
    RESEARCH = "research"
    REFERENCE = "reference"
    CODING_STANDARD = "coding_standard"
    SECURITY_STANDARD = "security_standard"
    DEPLOYMENT_GUIDE = "deployment_guide"
    TROUBLESHOOTING_GUIDE = "troubleshooting_guide"
    PROJECT_DOCUMENTATION = "project_documentation"
    LESSONS_LEARNED = "lessons_learned"
    POLICY = "policy"
    TEMPLATE = "template"


class KnowledgeStatus(str, Enum):
    """Document lifecycle status."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ReviewDecision(str, Enum):
    """Outcome of a knowledge review."""

    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class RelationshipType(str, Enum):
    """How one document relates to another in the knowledge graph."""

    RELATES_TO = "relates_to"
    REFERENCES = "references"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
    IMPLEMENTS = "implements"
    DERIVED_FROM = "derived_from"
    PART_OF = "part_of"


class ReferenceEntityType(str, Enum):
    """The kind of organizational entity a document links to (knowledge graph)."""

    PROJECT = "project"
    EMPLOYEE = "employee"
    AI_EMPLOYEE = "ai_employee"
    TASK = "task"
    SOP = "sop"
    ARCHITECTURE = "architecture"
    REPOSITORY = "repository"
    STANDARD = "standard"
    DECISION_RECORD = "decision_record"
    REFERENCE = "reference"


class SourceType(str, Enum):
    """Provenance of a knowledge document."""

    INTERNAL = "internal"
    EXTERNAL = "external"
    REPOSITORY = "repository"
    MEETING = "meeting"
    IMPORTED = "imported"


class AccessAction(str, Enum):
    """Access-log action types (analytics + usage tracking)."""

    VIEW = "view"
    RETRIEVE = "retrieve"
    CREATE = "create"
    UPDATE = "update"
    APPROVE = "approve"


class ADRStatus(str, Enum):
    """Architecture Decision Record status."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"
