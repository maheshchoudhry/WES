"""Seed data for the Organizational Knowledge Engine (Sprint 10).

Populates the knowledge base that every AI execution retrieves from: the twelve
categories, a spread of documents across the supported types (company overview,
coding standard, security standard, architecture, SOP index, lessons learned, a
template, project documentation), a knowledge graph (relationships + references
to the WORLD project and AI employees), two ADRs, and a curated collection. One
document is approved so the founder dashboard shows real coverage.

Idempotent: keyed on category code / document code / ADR code / collection slug.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.knowledge_enums import (
    ADRStatus,
    DocumentType,
    KnowledgeStatus,
    ReferenceEntityType,
    RelationshipType,
)
from app.models.ai import AIEmployee
from app.models.employee import Employee
from app.models.knowledge import (
    ArchitectureDecisionRecord,
    KnowledgeCategory,
    KnowledgeCollection,
    KnowledgeCollectionItem,
    KnowledgeDocument,
    KnowledgeEmbeddingPlaceholder,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeVersion,
)
from app.models.work import Project

# code, name, description
CATEGORIES = [
    ("KC-COMPANY", "Company", "Company-wide knowledge and identity"),
    ("KC-ENGINEERING", "Engineering", "Engineering practices and standards"),
    ("KC-AI", "AI", "AI systems, prompts, and orchestration"),
    ("KC-PROJECTS", "Projects", "Project documentation and context"),
    ("KC-ARCHITECTURE", "Architecture", "System architecture and decisions"),
    ("KC-DEVELOPMENT", "Development", "Development workflow and tooling"),
    ("KC-TESTING", "Testing", "Testing strategy and quality"),
    ("KC-SECURITY", "Security", "Security standards and policies"),
    ("KC-DEVOPS", "DevOps", "Deployment, CI/CD, and operations"),
    ("KC-DOCUMENTATION", "Documentation", "Documentation and knowledge practices"),
    ("KC-BUSINESS", "Business", "Business operations and strategy"),
    ("KC-OPERATIONS", "Operations", "Day-to-day operational knowledge"),
]

# code, title, doc_type, category_code, summary, keywords, content
DOCUMENTS = [
    (
        "KB-0001",
        "WES Company Overview",
        DocumentType.PROJECT_DOCUMENTATION,
        "KC-COMPANY",
        "Who WES is and how the AI company operates.",
        "company overview identity mission",
        "WORLD Engineering Studio is an AI engineering company that designs, manages, "
        "reviews, and builds software with the discipline of a professional studio.",
    ),
    (
        "KB-0002",
        "Backend Coding Standard",
        DocumentType.CODING_STANDARD,
        "KC-ENGINEERING",
        "Python/FastAPI conventions every engineer follows.",
        "coding standard python fastapi layering",
        "Layered architecture: API -> Service -> Repository -> ORM. Use the standard "
        "{data, meta} / {error} envelope. Type everything. Keep business logic provider- "
        "and framework-independent.",
    ),
    (
        "KB-0003",
        "Security Standard",
        DocumentType.SECURITY_STANDARD,
        "KC-SECURITY",
        "Baseline security requirements for all work.",
        "security secrets rbac auth",
        "Never commit secrets. Enforce RBAC on every endpoint. Hash passwords with bcrypt. "
        "Validate all input. No real API keys in the repository.",
    ),
    (
        "KB-0004",
        "System Architecture Overview",
        DocumentType.ARCHITECTURE,
        "KC-ARCHITECTURE",
        "The WES OS backend/frontend architecture.",
        "architecture fastapi react layering",
        "FastAPI + SQLAlchemy + Alembic backend; React + Vite + TypeScript frontend. "
        "Portable UUID PKs, migrations 0001-0007, provider-independent orchestration.",
    ),
    (
        "KB-0005",
        "Engineering SOP Index",
        DocumentType.SOP,
        "KC-DEVELOPMENT",
        "Index of standard operating procedures for engineering.",
        "sop procedure code review test deploy",
        "SOP-CODE (implementation), SOP-REVIEW (review), SOP-TEST (testing), "
        "SOP-DEPLOY (deployment), SOP-DOCS (documentation), SOP-SEC (security).",
    ),
    (
        "KB-0006",
        "Lessons Learned: Runtime Verification",
        DocumentType.LESSONS_LEARNED,
        "KC-OPERATIONS",
        "Always verify at runtime, not just at implementation.",
        "lessons learned runtime verification decisions",
        "A sprint is not complete until the backend starts, the frontend loads, migrations "
        "apply, and browser flows are verified. Fix every runtime issue before declaring done.",
    ),
    (
        "KB-0007",
        "Document Template: ADR",
        DocumentType.TEMPLATE,
        "KC-DOCUMENTATION",
        "Reusable template for architecture decision records.",
        "template adr decision record",
        "Context: <why>. Decision: <what>. Consequences: <tradeoffs>. Status: proposed | "
        "accepted | superseded.",
    ),
    (
        "KB-0008",
        "WORLD Project Documentation",
        DocumentType.PROJECT_DOCUMENTATION,
        "KC-PROJECTS",
        "Context and scope for the WORLD project.",
        "world project scope repository",
        "WORLD is the flagship project delivered by the WES AI workforce. Repository: "
        "github.com/wes/world. Delivered sprint-by-sprint with full runtime verification.",
    ),
]

# source_code, target_code, relationship_type, note
RELATIONSHIPS = [
    (
        "KB-0002",
        "KB-0004",
        RelationshipType.IMPLEMENTS,
        "Coding standard implements the architecture",
    ),
    (
        "KB-0004",
        "KB-0003",
        RelationshipType.DEPENDS_ON,
        "Architecture depends on the security standard",
    ),
    ("KB-0005", "KB-0002", RelationshipType.REFERENCES, "SOP index references the coding standard"),
    (
        "KB-0008",
        "KB-0001",
        RelationshipType.PART_OF,
        "Project docs are part of the company knowledge",
    ),
    ("KB-0007", "KB-0004", RelationshipType.RELATES_TO, "ADR template relates to architecture"),
]

# code, title, status, context, decision, consequences, document_code
ADRS = [
    (
        "ADR-0001",
        "Provider-Independent AI Orchestration",
        ADRStatus.ACCEPTED,
        "AI executions must not be coupled to any single LLM provider.",
        "Introduce a Provider Abstraction Layer; business logic talks only to the interface.",
        "Adding a provider requires only a new adapter + API key; no business-logic change.",
        "KB-0004",
    ),
    (
        "ADR-0002",
        "Knowledge as the Single Source of Truth",
        ADRStatus.ACCEPTED,
        "AI employees need consistent organizational knowledge before deciding.",
        "Every AI execution retrieves relevant documents/SOPs/ADRs/standards before running.",
        "Knowledge becomes a first-class asset; future semantic search plugs in unchanged.",
        None,
    ),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def seed_knowledge(db: Session) -> None:
    """Seed categories, documents, graph, ADRs, and a collection. Idempotent."""
    # Skip if already seeded.
    if db.scalar(select(KnowledgeCategory).where(KnowledgeCategory.code == "KC-COMPANY")):
        return

    author = db.scalar(select(Employee).order_by(Employee.employee_code))  # may be None in tests
    author_id = author.id if author else None
    owner = db.scalar(select(AIEmployee).where(AIEmployee.employee_code == "AI-EMP-003"))
    project = db.scalar(select(Project).where(Project.code == "PROJECT-001"))

    # Categories.
    cats: dict[str, KnowledgeCategory] = {}
    for i, (code, name, desc) in enumerate(CATEGORIES):
        c = KnowledgeCategory(code=code, name=name, description=desc, position=i)
        db.add(c)
        cats[code] = c
    db.flush()

    # Documents (+ initial version + embedding placeholder).
    docs: dict[str, KnowledgeDocument] = {}
    for code, title, dtype, cat_code, summary, keywords, content in DOCUMENTS:
        doc = KnowledgeDocument(
            code=code,
            slug=code.lower(),
            title=title,
            doc_type=dtype.value,
            category_id=cats[cat_code].id,
            summary=summary,
            keywords=keywords,
            content=content,
            status=KnowledgeStatus.DRAFT,
            version=1,
            author_id=author_id,
            owner_ai_employee_id=owner.id if owner else None,
        )
        db.add(doc)
        db.flush()
        db.add(
            KnowledgeVersion(
                document_id=doc.id,
                version=1,
                title=title,
                content=content,
                change_summary="Initial version",
                status=KnowledgeStatus.DRAFT.value,
                author_id=author_id,
            )
        )
        db.add(
            KnowledgeEmbeddingPlaceholder(
                document_id=doc.id, status="pending", note="Awaiting semantic-search backend"
            )
        )
        docs[code] = doc
    db.flush()

    # Approve a few core documents so the base is authoritative + dashboard is real.
    for code in ("KB-0001", "KB-0002", "KB-0003", "KB-0004"):
        d = docs[code]
        d.status = KnowledgeStatus.APPROVED
        d.approver_id = author_id
        d.approved_at = _now()
        d.view_count = {"KB-0002": 12, "KB-0004": 9, "KB-0003": 5, "KB-0001": 3}[code]
    # Leave one document in review so the review center has work.
    docs["KB-0005"].status = KnowledgeStatus.IN_REVIEW
    db.flush()

    # Relationships (knowledge graph edges between documents).
    for src, tgt, rtype, note in RELATIONSHIPS:
        db.add(
            KnowledgeRelationship(
                source_document_id=docs[src].id,
                target_document_id=docs[tgt].id,
                relationship_type=rtype.value,
                note=note,
            )
        )

    # References (knowledge graph edges to organizational entities).
    if project is not None:
        db.add(
            KnowledgeReference(
                document_id=docs["KB-0008"].id,
                entity_type=ReferenceEntityType.PROJECT.value,
                entity_id=project.id,
                label="WORLD project",
            )
        )
    if owner is not None:
        db.add(
            KnowledgeReference(
                document_id=docs["KB-0004"].id,
                entity_type=ReferenceEntityType.AI_EMPLOYEE.value,
                entity_id=owner.id,
                label="Chief Architect (owner)",
            )
        )
    db.add(
        KnowledgeReference(
            document_id=docs["KB-0005"].id,
            entity_type=ReferenceEntityType.SOP.value,
            entity_id=None,
            label="SOP-CODE / SOP-REVIEW / SOP-TEST",
        )
    )
    db.flush()

    # ADRs.
    adrs: dict[str, ArchitectureDecisionRecord] = {}
    for code, title, status, context, decision, consequences, doc_code in ADRS:
        adr = ArchitectureDecisionRecord(
            code=code,
            title=title,
            status=status.value,
            context=context,
            decision=decision,
            consequences=consequences,
            document_id=docs[doc_code].id if doc_code else None,
            project_id=project.id if project else None,
            decided_by_id=author_id,
            decided_at=_now(),
        )
        db.add(adr)
        adrs[code] = adr
    db.flush()

    # A curated collection: engineering essentials.
    collection = KnowledgeCollection(
        slug="engineering-essentials",
        name="Engineering Essentials",
        description="Core standards and architecture every engineer must know.",
        owner_id=author_id,
    )
    db.add(collection)
    db.flush()
    for pos, code in enumerate(("KB-0002", "KB-0003", "KB-0004", "KB-0005")):
        db.add(
            KnowledgeCollectionItem(
                collection_id=collection.id, document_id=docs[code].id, position=pos
            )
        )
    db.flush()
