# WES OS — Implementation Documentation

Implementation documentation for **WES OS**, the WES Operating System. This is
distinct from the [Blueprint](../../Blueprint/README.md) (the frozen operating
framework) — it documents the software as built.

## Modules

| Sprint | Module | Status |
|--------|--------|--------|
| Sprint 02 | [Core Company Engine](./company-engine.md) — Company, Departments, Employees | Implemented |
| Sprint 03 | [Founder Workspace & Executive Dashboard](./dashboard.md) | Implemented |
| Sprint 04 | [Authentication & RBAC](./auth.md) | Implemented |
| Sprint 06 | [AI Company Core](./ai-company.md) | Implemented |
| Sprint 07 | [AI Work Management](./work-management.md) | Implemented |
| Sprint 08 | [AI Execution Engine](./execution-engine.md) | Implemented |
| Sprint 09 | [AI Orchestration & Provider Abstraction](./orchestration-engine.md) | Implemented |
| Sprint 10 | [Organizational Knowledge Engine](./knowledge-engine.md) | Implemented |
| Sprint 11 | [Live AI Provider Integration Platform](./provider-platform.md) | Implemented |
| Sprint 12 | [Repository Intelligence & Code Understanding](./repository-intelligence.md) | Implemented |
| Sprint 13 | [Autonomous Software Development Engine](./development-engine.md) | Implemented |

## Contents

- [Company Engine](./company-engine.md) — architecture, domain model, business rules
- [Founder Dashboard](./dashboard.md) — dashboard aggregation, widgets, screenshots
- [Authentication & RBAC](./auth.md) — JWT auth, roles/permissions, login flow
- [AI Company Core](./ai-company.md) — AI organization: employees, roles, org chart
- [AI Work Management](./work-management.md) — projects, sprints, tasks, Kanban, assignments
- [AI Execution Engine](./execution-engine.md) — workspaces, queue, libraries, handoffs
- [AI Orchestration & Provider Abstraction](./orchestration-engine.md) — pipeline, providers, conversation, memory
- [Organizational Knowledge Engine](./knowledge-engine.md) — documents, knowledge graph, search, AI retrieval
- [Live AI Provider Integration Platform](./provider-platform.md) — real providers, secrets, streaming, failover, budget
- [Repository Intelligence & Code Understanding](./repository-intelligence.md) — scanner, parser, symbols, graphs, impact
- [Autonomous Software Development Engine](./development-engine.md) — plan, generate, test, review, git, PR, approval
- [API Reference](./api.md) — every REST endpoint, request/response shapes, error codes
- [Setup Guide](./setup.md) — run locally and with Docker

## Codebase

| Path | Description |
|------|-------------|
| [`/backend`](../../backend/README.md) | FastAPI + SQLAlchemy + Alembic service |
| [`/frontend`](../../frontend/README.md) | React + Vite + TypeScript UI |
| [`/docker-compose.yml`](../../docker-compose.yml) | Postgres + backend + frontend orchestration |
