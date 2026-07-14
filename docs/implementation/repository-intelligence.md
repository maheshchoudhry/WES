# Repository Intelligence & Code Understanding Engine (Sprint 12)

The software-understanding layer of WES. It scans **real repositories**, parses
source code, and builds a queryable model — files, modules, symbols, dependency
graphs, architecture layers, a search index, metrics, issues, and TODOs — so every
AI employee can understand a codebase **before** writing or reviewing code. This
sprint implements understanding only (no autonomous coding).

Verified on the WES backend itself: **113 files, 1132 symbols, 169 routes, 73
models**, architecture auto-classified into service/api/repository/model/schema/
utility layers.

## Repository architecture

```
Scanner → Parser → Indexer → { Files · Modules · Symbols · Dependencies ·
  Relationships · Architecture · Search Index · Metrics · Issues · TODOs }
        → Symbol / Dependency / Search / Impact / Architecture / Documentation
        → AI retrieval (repository context before code work)
```

Layered as everywhere: services over ORM, `{data, meta}` envelope, portable UUIDs.

## Parser (`app/services/repo_parser.py`)

Pure, dependency-free, per-language extraction:

- **Python** — standard-library `ast`: classes (Model/Schema/Enum inferred from
  bases), functions/methods, **routes** (from `@router.get`-style decorators),
  constants, imports (internal vs external), inheritance relationships,
  docstrings, and signatures.
- **TypeScript / JavaScript** — focused parsing of imports, `export function`,
  `class`, `interface`, `type`, and React components (PascalCase in `.tsx`).
- **JSON / package.json** (dependencies), **requirements.txt**, **Dockerfile**
  (`FROM`), **SQL** (`CREATE TABLE`), **YAML**, **Markdown** (headings).
- TODO/FIXME/XXX/HACK extraction across all languages.

Supported languages: Python, TypeScript, JavaScript, JSON, YAML, Markdown,
Dockerfile, SQL, requirements, package.json.

## Scanner (`app/services/repo_scanner.py`)

Walks the tree, pruning ignored dirs (`.git`, `node_modules`, `.venv`,
`__pycache__`, `dist`, caches…), and classifies each file: language, module,
architecture layer, and config / generated / test flags. Only parseable source is
read; the rest is inventoried.

## Indexer (`app/services/repository_service.py`)

The scan pipeline (idempotent re-index): scan → parse → persist files, modules,
symbols, dependencies, relationships, per-layer architecture, a denormalized
search index, metrics (counts, languages, technical debt, health score), issues,
and TODOs. `RepositoryScan` records status/counts/duration.

## Symbol index

Every symbol stores name, type, file, line/end-line, parent, signature, and
docstring — powering the symbol browser and cross-reference (`/references`).

## Dependency graph

- **Import graph** — file → file internal imports (`/import-graph`).
- **Module graph** — aggregated to directory/package level (`/module-graph`).
- **External packages** — usage counts (`/dependencies`).

## Architecture analysis

Files are classified into layers (frontend, api, service, model, schema,
repository, utility, configuration, test, migration, documentation) from path +
content, then aggregated into `repository_architecture` with file/symbol counts.

## Search (`SearchService`)

Unified repository search over the denormalized index — file / class / function /
method / route / model / component — LIKE-based today with a stable signature and
row shape so a semantic/vector backend drops in without changing callers.

## Impact analysis (`ImpactAnalysisService`)

Given a file, returns its dependencies, dependents (potential breakages), related
tests, related APIs (routes it defines), and related documentation (Knowledge
Engine references). Verified: `services/orchestration.py` → 12 deps, 7 dependents.

## Documentation

`DocumentationService` connects source to the Knowledge Engine (repository
references) and markdown docs, tying code to ADRs/SOPs/architecture docs.

## AI retrieval (before code work)

The orchestration `ContextBuilder` calls `RepositoryRetrievalService.retrieve_for`
with task/role keywords, assembling the repository, relevant files/symbols, and
architecture into the prompt — resilient when nothing is scanned yet.

## Database changes — migration `0009` (13 tables)

`repositories`, `repository_scans`, `repository_modules`, `repository_files`,
`repository_symbols`, `repository_dependencies`, `repository_relationships`,
`repository_architecture`, `repository_search_index`, `repository_change_history`,
`repository_metrics`, `repository_issues`, `repository_todos`.

## API endpoints (`/repositories`)

| Method | Path |
|--------|------|
| GET/POST | `/`, `/{id}` |
| POST | `/{id}/scan` |
| GET | `/{id}/dashboard`, `/{id}/files`, `/{id}/modules`, `/{id}/architecture` |
| GET | `/{id}/symbols`, `/{id}/files/{file_id}/symbols`, `/{id}/references` |
| GET | `/{id}/import-graph`, `/{id}/module-graph`, `/{id}/dependencies` |
| GET | `/{id}/search`, `/{id}/impact`, `/{id}/documentation`, `/{id}/ai-context` |

## RBAC (reuses Sprint 04)

`repo:read` → all roles (browse, search, impact, dashboards). `repo:write`
(register, scan) → **Founder only**.

## Frontend

Repository Dashboard, Explorer (files → symbols), Architecture Explorer,
Dependency Graph, Symbol Browser, Impact Analysis, Code Search, Module Explorer —
plus a founder-dashboard widget and nav.

## Seed

Registers the WES backend `app` package as a repository and runs one real scan, so
the engine ships with genuine intelligence AI employees can retrieve. Idempotent.

## Toward autonomous development (future-proofing)

The data model and APIs are stable seams: symbols, graphs, impact, and search are
already the substrate an autonomous coding engine would consume. A future sprint
can add generation/review on top without changing this engine's schema or APIs.
