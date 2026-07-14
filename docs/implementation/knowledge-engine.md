# Organizational Knowledge Engine (Sprint 10)

The intelligence layer of WES and its **single source of truth**. Knowledge is a
first-class asset: every AI execution retrieves the relevant documents, SOPs,
ADRs, standards, previous decisions, references, and templates **before** it runs.

No LLM integration and no external vector database in this build. The data model
and public APIs are designed so semantic/vector retrieval can be added later
**without changing either** — the `knowledge_embeddings_placeholder` table and the
`SearchService.search()` seam reserve that extension point.

## Knowledge architecture

```
Document ── category / tags / status / versions
   │
   ├─ relationships ──► other documents      (knowledge graph, doc↔doc)
   ├─ references ─────► projects, employees,  (knowledge graph, doc↔entity)
   │                    AI employees, tasks, SOPs, architecture,
   │                    repositories, standards, decision records
   ├─ reviews ───────► approval workflow (drives status)
   ├─ access log ────► analytics + AI retrieval tracking
   └─ embeddings placeholder ─► future semantic search (no vectors stored)
```

Layered as everywhere in WES: **API → Service → ORM**, standard `{data, meta}` /
`{error}` envelope, portable UUID PKs.

## Document types (17)

architecture · adr · sop · specification · api · design · meeting_notes ·
research · reference · coding_standard · security_standard · deployment_guide ·
troubleshooting_guide · project_documentation · lessons_learned · policy · template

## Categories (12, seeded)

Company · Engineering · AI · Projects · Architecture · Development · Testing ·
Security · DevOps · Documentation · Business · Operations

## Services

| Service | Responsibility |
|---------|----------------|
| `KnowledgeService` | Document CRUD, serialization, view/access logging |
| `CategoryService` / `TagService` | Taxonomy + tagging (counts per category) |
| `RelationshipService` | Doc↔doc graph edges; graph nodes/edges; related docs |
| `ReferenceService` | Doc↔entity graph edges (projects, employees, SOPs, …) |
| `VersionService` | Version history + non-destructive restore |
| `SearchService` | Keyword / full-text / category / tag / status search |
| `RetrievalService` | AI pre-execution knowledge bundle |
| `ApprovalService` | Submit → review → approve/reject; pending queue |
| `AnalyticsService` | Founder & AI dashboards, statistics |
| `ADRService` | Architecture Decision Record registry |
| `BookmarkService` / `CollectionService` | Per-user favorites + curated sets |

## Versioning

Every content change snapshots a `knowledge_versions` row (version, title,
content, change summary, author, status). History is newest-first; **restore**
re-applies a prior version as a new current version (never destructive).

## Search engine

`SearchService.search()` is the single entry point: keyword + full-text `LIKE`
matching over title/summary/content/keywords/code, plus category, doc-type, tag,
and status filters. The signature and result shape are backend-agnostic — a
vector backend can replace the matching internally without touching callers.

Also supported: recent documents, most-used (by views), favorites (bookmarks),
collections, and related documents (graph traversal).

## AI retrieval (before every execution)

The orchestration `ContextBuilder` calls `RetrievalService.retrieve_for()` with
keywords derived from the task and role. The returned bundle fills seven slots —
`relevant_documents`, `relevant_sop`, `relevant_adr`, `relevant_standards`,
`relevant_decisions`, `relevant_templates`, `relevant_references` — and is folded
into the prompt as a system message. Each retrieval is recorded in
`knowledge_access_log` (verified live: retrievals `0 → 11` after one run).

## Database changes

Migration `0007_organizational_knowledge_engine` — 13 primary tables plus 2
association tables: `knowledge_categories`, `knowledge_tags`,
`knowledge_documents`, `knowledge_document_tags` (join), `knowledge_relationships`,
`knowledge_versions`, `knowledge_reviews`, `knowledge_sources`,
`knowledge_references`, `knowledge_embeddings_placeholder`, `knowledge_access_log`,
`knowledge_bookmarks`, `knowledge_collections`, `knowledge_collection_items`
(join), `architecture_decision_records`.

## API endpoints (`/knowledge`)

| Method | Path |
|--------|------|
| GET/POST | `/documents`, `/documents/{id}` (GET view), PATCH `/documents/{id}` |
| GET | `/documents/{id}/versions`, `/documents/{id}/related`, `/documents/{id}/reviews` |
| POST | `/documents/{id}/versions/{v}/restore`, `/documents/{id}/submit`, `/documents/{id}/references` |
| POST | `/documents/{id}/review` (approve/reject) |
| GET/POST | `/categories`, GET `/tags` |
| GET | `/search`, `/retrieve` |
| GET/POST/DELETE | `/relationships`, `/graph` (GET) |
| GET/POST/PATCH | `/adrs`, `/adrs/{id}/status` |
| GET/POST/DELETE | `/bookmarks` |
| GET/POST | `/collections`, `/collections/{id}` (+ documents) |
| GET | `/reviews/pending`, `/founder-dashboard`, `/ai-dashboard`, `/analytics` |

## Knowledge graph

- **Document ↔ document** via `knowledge_relationships` (relates_to, references,
  supersedes, depends_on, implements, derived_from, part_of).
- **Document ↔ entity** via `knowledge_references` (project, employee, ai_employee,
  task, sop, architecture, repository, standard, decision_record, reference).
- `/graph` returns nodes + edges for visualization; every edge is queryable.

## RBAC (reuses Sprint 04)

`knowledge:read` → all authenticated roles (and AI employees). `knowledge:write`
(author/edit documents, ADRs, collections) → Founder, Director, Department Head
(the authoring roles, incl. Technical Writer authoring). `knowledge:approve`
(approve/reject reviews) → Founder, Director. Unauthenticated → 401.

## Dashboards

- **Founder** — document/category/ADR counts, approved coverage, pending reviews,
  recent + most-used documents, documents-by-type, knowledge health.
- **AI** — suggested knowledge, recent knowledge, architecture references, coding
  standards, SOP recommendations, organization memory, related documents.

## Seed data

12 categories, 8 documents spanning the types (4 approved, 1 in review), a 5-edge
document graph, references to the WORLD project and the Chief Architect, 2 ADRs,
and the "Engineering Essentials" collection. Idempotent.

## Adding semantic search later (no breaking changes)

1. Populate real vectors against `knowledge_embeddings_placeholder` rows.
2. Swap the `LIKE` matching inside `SearchService.search()` for a vector query.
The signature, result shape, `/search`, `/retrieve`, and every caller stay identical.
