"""Organizational Knowledge Engine endpoints (Sprint 10).

Documents (CRUD + versions), categories, tags, the knowledge graph
(relationships + references), search, AI retrieval, reviews/approvals,
bookmarks, collections, ADRs, and the founder/AI dashboards.

RBAC: read → all authenticated roles; write (author/edit) → knowledge:write;
approvals → knowledge:approve.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import (
    CurrentUser,
    get_adr_service,
    get_approval_service,
    get_bookmark_service,
    get_collection_service,
    get_current_user,
    get_knowledge_analytics_service,
    get_knowledge_graph_service,
    get_knowledge_service,
    get_reference_service,
    get_retrieval_service,
    get_search_service,
    get_version_service,
    require_permission,
)
from app.domain.knowledge_enums import (
    ADRStatus,
    DocumentType,
    ReferenceEntityType,
    RelationshipType,
    ReviewDecision,
)
from app.domain.roles import Permission

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
_read = Depends(require_permission(Permission.KNOWLEDGE_READ))
_write = Depends(require_permission(Permission.KNOWLEDGE_WRITE))
_approve = Depends(require_permission(Permission.KNOWLEDGE_APPROVE))


# --- payloads -------------------------------------------------------------


class DocumentIn(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    doc_type: DocumentType
    content: str = ""
    summary: str | None = None
    category_id: uuid.UUID | None = None
    keywords: str | None = None
    owner_ai_employee_id: uuid.UUID | None = None
    tags: list[str] | None = None


class DocumentUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=300)
    content: str | None = None
    summary: str | None = None
    category_id: uuid.UUID | None = None
    keywords: str | None = None
    tags: list[str] | None = None
    change_summary: str | None = None


class CategoryIn(BaseModel):
    code: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    position: int = 0


class RelationshipIn(BaseModel):
    source_document_id: uuid.UUID
    target_document_id: uuid.UUID
    relationship_type: RelationshipType
    note: str | None = None


class ReferenceIn(BaseModel):
    entity_type: ReferenceEntityType
    entity_id: uuid.UUID | None = None
    label: str | None = None


class ReviewIn(BaseModel):
    decision: ReviewDecision
    comment: str | None = None


class BookmarkIn(BaseModel):
    document_id: uuid.UUID
    note: str | None = None


class CollectionIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None


class CollectionDocumentIn(BaseModel):
    document_id: uuid.UUID


class ADRIn(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    context: str | None = None
    decision: str | None = None
    consequences: str | None = None
    status: ADRStatus = ADRStatus.PROPOSED
    document_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None


class ADRStatusIn(BaseModel):
    status: ADRStatus


# --- categories & tags ----------------------------------------------------


@router.get("/categories", dependencies=[_read])
def list_categories(service=Depends(get_knowledge_service)) -> dict:
    items = service.categories.with_counts()
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/categories", dependencies=[_write])
def create_category(payload: CategoryIn, service=Depends(get_knowledge_service)) -> dict:
    c = service.categories.create(payload.code, payload.name, payload.description, payload.position)
    return {"data": service.categories.serialize(c, 0)}


@router.get("/tags", dependencies=[_read])
def list_tags(service=Depends(get_knowledge_service)) -> dict:
    items = [service.tags.serialize(t) for t in service.tags.list_tags()]
    return {"data": items, "meta": {"total": len(items)}}


# --- search & retrieval ---------------------------------------------------


@router.get("/search", dependencies=[_read])
def search(
    q: str | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    doc_type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    status: str | None = Query(default=None),
    knowledge=Depends(get_knowledge_service),
    search_service=Depends(get_search_service),
) -> dict:
    docs = search_service.search(
        q, category_id=category_id, doc_type=doc_type, tag=tag, status=status
    )
    items = [knowledge.serialize(d) for d in docs]
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/retrieve", dependencies=[_read])
def retrieve(
    keywords: str | None = Query(default=None),
    ai_employee_id: uuid.UUID | None = Query(default=None),
    service=Depends(get_retrieval_service),
) -> dict:
    return {"data": service.retrieve_for(keywords=keywords, ai_employee_id=ai_employee_id)}


# --- dashboards -----------------------------------------------------------


@router.get("/founder-dashboard", dependencies=[_read])
def founder_dashboard(service=Depends(get_knowledge_analytics_service)) -> dict:
    return {"data": service.founder_dashboard()}


@router.get("/ai-dashboard", dependencies=[_read])
def ai_dashboard(
    keywords: str | None = Query(default=None),
    service=Depends(get_knowledge_analytics_service),
) -> dict:
    return {"data": service.ai_dashboard(keywords)}


@router.get("/analytics", dependencies=[_read])
def analytics(service=Depends(get_knowledge_analytics_service)) -> dict:
    return {"data": service.statistics()}


# --- knowledge graph ------------------------------------------------------


@router.get("/graph", dependencies=[_read])
def graph(service=Depends(get_knowledge_graph_service)) -> dict:
    return {"data": service.graph()}


@router.post("/relationships", dependencies=[_write])
def create_relationship(
    payload: RelationshipIn, service=Depends(get_knowledge_graph_service)
) -> dict:
    rel = service.link(
        payload.source_document_id,
        payload.target_document_id,
        payload.relationship_type,
        payload.note,
    )
    return {"data": service.serialize(rel)}


@router.delete("/relationships/{relationship_id}", dependencies=[_write])
def delete_relationship(
    relationship_id: uuid.UUID, service=Depends(get_knowledge_graph_service)
) -> dict:
    service.unlink(relationship_id)
    return {"data": {"deleted": str(relationship_id)}}


# --- reviews (pending list at the collection level) -----------------------


@router.get("/reviews/pending", dependencies=[_read])
def pending_reviews(service=Depends(get_approval_service)) -> dict:
    from app.services.knowledge import KnowledgeService

    ks = KnowledgeService(service.db)
    items = [ks.serialize(d) for d in service.pending_reviews()]
    return {"data": items, "meta": {"total": len(items)}}


# --- ADRs -----------------------------------------------------------------


@router.get("/adrs", dependencies=[_read])
def list_adrs(service=Depends(get_adr_service)) -> dict:
    items = [service.serialize(a) for a in service.list_adrs()]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/adrs", dependencies=[_write])
def create_adr(payload: ADRIn, service=Depends(get_adr_service)) -> dict:
    adr = service.create(
        title=payload.title,
        context=payload.context,
        decision=payload.decision,
        consequences=payload.consequences,
        status=payload.status,
        document_id=payload.document_id,
        project_id=payload.project_id,
    )
    return {"data": service.serialize(adr)}


@router.patch("/adrs/{adr_id}/status", dependencies=[_write])
def set_adr_status(
    adr_id: uuid.UUID, payload: ADRStatusIn, service=Depends(get_adr_service)
) -> dict:
    return {"data": service.serialize(service.set_status(adr_id, payload.status))}


# --- bookmarks ------------------------------------------------------------


@router.get("/bookmarks", dependencies=[_read])
def list_bookmarks(
    user: CurrentUser = Depends(get_current_user), service=Depends(get_bookmark_service)
) -> dict:
    items = [service.serialize(b) for b in service.list_for_user(user.id)]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/bookmarks", dependencies=[_read])
def add_bookmark(
    payload: BookmarkIn,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_bookmark_service),
) -> dict:
    bm = service.add(user.id, payload.document_id, payload.note)
    return {"data": service.serialize(bm)}


@router.delete("/bookmarks/{document_id}", dependencies=[_read])
def remove_bookmark(
    document_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_bookmark_service),
) -> dict:
    service.remove(user.id, document_id)
    return {"data": {"removed": str(document_id)}}


# --- collections ----------------------------------------------------------


@router.get("/collections", dependencies=[_read])
def list_collections(service=Depends(get_collection_service)) -> dict:
    items = [service.serialize(c) for c in service.list_collections()]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/collections", dependencies=[_write])
def create_collection(
    payload: CollectionIn,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_collection_service),
) -> dict:
    c = service.create(payload.name, description=payload.description, owner_id=user.id)
    return {"data": service.serialize(c)}


@router.get("/collections/{collection_id}", dependencies=[_read])
def get_collection(collection_id: uuid.UUID, service=Depends(get_collection_service)) -> dict:
    return {"data": service.serialize(service.get(collection_id), with_documents=True)}


@router.post("/collections/{collection_id}/documents", dependencies=[_write])
def add_to_collection(
    collection_id: uuid.UUID,
    payload: CollectionDocumentIn,
    service=Depends(get_collection_service),
) -> dict:
    c = service.add_document(collection_id, payload.document_id)
    return {"data": service.serialize(c, with_documents=True)}


@router.delete("/collections/{collection_id}/documents/{document_id}", dependencies=[_write])
def remove_from_collection(
    collection_id: uuid.UUID, document_id: uuid.UUID, service=Depends(get_collection_service)
) -> dict:
    service.remove_document(collection_id, document_id)
    return {"data": service.serialize(service.get(collection_id), with_documents=True)}


# --- documents ------------------------------------------------------------


@router.get("/documents", dependencies=[_read])
def list_documents(
    category_id: uuid.UUID | None = Query(default=None),
    doc_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service=Depends(get_knowledge_service),
) -> dict:
    docs = service.list_documents(category_id=category_id, doc_type=doc_type, status=status)
    items = [service.serialize(d) for d in docs]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/documents", dependencies=[_write])
def create_document(
    payload: DocumentIn,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_knowledge_service),
) -> dict:
    doc = service.create(
        title=payload.title,
        doc_type=payload.doc_type,
        content=payload.content,
        summary=payload.summary,
        category_id=payload.category_id,
        keywords=payload.keywords,
        author_id=user.id,
        owner_ai_employee_id=payload.owner_ai_employee_id,
        tags=payload.tags,
    )
    return {"data": service.serialize(doc, full=True)}


@router.get("/documents/{document_id}", dependencies=[_read])
def get_document(
    document_id: uuid.UUID,
    graph=Depends(get_knowledge_graph_service),
    references=Depends(get_reference_service),
    service=Depends(get_knowledge_service),
) -> dict:
    doc = service.view(document_id)
    data = service.serialize(doc, full=True)
    data["relationships"] = [graph.serialize(r) for r in graph.for_document(document_id)]
    data["references"] = [references.serialize(r) for r in references.for_document(document_id)]
    return {"data": data}


@router.patch("/documents/{document_id}", dependencies=[_write])
def update_document(
    document_id: uuid.UUID, payload: DocumentUpdateIn, service=Depends(get_knowledge_service)
) -> dict:
    doc = service.update(
        document_id,
        title=payload.title,
        content=payload.content,
        summary=payload.summary,
        category_id=payload.category_id,
        keywords=payload.keywords,
        tags=payload.tags,
        change_summary=payload.change_summary,
    )
    return {"data": service.serialize(doc, full=True)}


@router.get("/documents/{document_id}/versions", dependencies=[_read])
def document_versions(document_id: uuid.UUID, service=Depends(get_version_service)) -> dict:
    items = [service.serialize(v) for v in service.history(document_id)]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/documents/{document_id}/versions/{version}/restore", dependencies=[_write])
def restore_version(
    document_id: uuid.UUID,
    version: int,
    version_service=Depends(get_version_service),
    knowledge=Depends(get_knowledge_service),
) -> dict:
    doc = version_service.restore(document_id, version)
    return {"data": knowledge.serialize(doc, full=True)}


@router.get("/documents/{document_id}/related", dependencies=[_read])
def related_documents(
    document_id: uuid.UUID,
    graph=Depends(get_knowledge_graph_service),
    knowledge=Depends(get_knowledge_service),
) -> dict:
    items = [knowledge.serialize(d) for d in graph.related_documents(document_id)]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/documents/{document_id}/references", dependencies=[_write])
def add_reference(
    document_id: uuid.UUID, payload: ReferenceIn, service=Depends(get_reference_service)
) -> dict:
    ref = service.add(document_id, payload.entity_type, payload.entity_id, payload.label)
    return {"data": service.serialize(ref)}


@router.post("/documents/{document_id}/submit", dependencies=[_write])
def submit_for_review(document_id: uuid.UUID, service=Depends(get_approval_service)) -> dict:
    from app.services.knowledge import KnowledgeService

    doc = service.submit_for_review(document_id)
    return {"data": KnowledgeService(service.db).serialize(doc)}


@router.get("/documents/{document_id}/reviews", dependencies=[_read])
def document_reviews(document_id: uuid.UUID, service=Depends(get_approval_service)) -> dict:
    items = [service.serialize(r) for r in service.reviews_for(document_id)]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/documents/{document_id}/review", dependencies=[_approve])
def review_document(
    document_id: uuid.UUID,
    payload: ReviewIn,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_approval_service),
) -> dict:
    review = service.review(
        document_id, payload.decision, reviewer_id=user.id, comment=payload.comment
    )
    return {"data": service.serialize(review)}
