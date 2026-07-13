# Architecture

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Frozen &nbsp;|&nbsp; **Owner:** WES Engineering

## Overall Architecture

The WES Web Application is a **decoupled, layered, module-based system** delivered as a monorepo with two deployable applications:

```
[ Browser ]
     │  HTTPS (REST/JSON, JWT)
     ▼
[ Frontend App ]  Next.js (React, TypeScript)
     │  API calls (/api/v1)
     ▼
[ Backend API ]   FastAPI (Python)
     │  ORM (SQLAlchemy)
     ▼
[ Database ]      PostgreSQL
```

The frontend and backend are independently deployable and communicate only over a versioned REST API. This separation keeps concerns clean, allows each side to scale independently, and lets AI capabilities (a core WES concern) live behind the API without leaking into the UI.

## Application Layers

**Backend (strict layering, dependencies point downward):**

| Layer | Responsibility |
|-------|----------------|
| **API / Routers** | HTTP endpoints, request/response, validation. No business logic. |
| **Services** | Business logic and use cases. Orchestrates repositories. |
| **Repositories** | Data access; the only layer that talks to the ORM. |
| **Models** | SQLAlchemy ORM entities (database mapping). |
| **Schemas** | Pydantic models for API input/output (separate from ORM). |
| **Core** | Config, security, shared utilities. |

**Frontend (feature-based):**

| Layer | Responsibility |
|-------|----------------|
| **App (routes)** | Next.js App Router pages and layouts. |
| **Features** | Self-contained modules (components, hooks, logic per domain). |
| **Components** | Shared, reusable UI components. |
| **Lib** | API client, utilities, configuration. |
| **Stores** | Client state (Zustand). |
| **Types** | Shared TypeScript types. |

## Module Structure

Each domain (Employees, Projects, Tasks, …) is a **vertical module** present on both sides: a backend slice (router → service → repository → model/schema) and a frontend feature folder. Modules are added without changing the core, supporting long-term scalability. Full list in the [Module Map](./03-Module-Map.md).

## Folder Structure

```
wes-app/
├─ docs/                     Engineering documentation (this set)
├─ frontend/                 Next.js application
│  └─ src/
│     ├─ app/                 App Router routes & layouts
│     ├─ features/            Domain modules (auth, employees, projects, …)
│     ├─ components/          Shared UI components
│     ├─ lib/                 API client, utilities
│     ├─ hooks/               Shared React hooks
│     ├─ stores/              Client state (Zustand)
│     ├─ types/               Shared TypeScript types
│     └─ styles/              Global styles
├─ backend/                  FastAPI application
│  ├─ app/
│  │  ├─ main.py              App entrypoint
│  │  ├─ core/                Config, security
│  │  ├─ api/v1/              Versioned routers
│  │  ├─ services/            Business logic
│  │  ├─ repositories/        Data access
│  │  ├─ models/              ORM entities
│  │  ├─ schemas/             Pydantic schemas
│  │  └─ db/                  Session & migrations base
│  └─ tests/                  Backend tests
└─ infra/                    Docker & local environment
```

## Naming Conventions

**Backend (Python):** `snake_case` for modules, functions, variables; `PascalCase` for classes; `snake_case` files. DB tables `snake_case` plural (e.g., `employees`).

**Frontend (TypeScript):** `PascalCase` for React components and types (`EmployeeCard.tsx`); `camelCase` for variables, functions, and hooks (`useEmployees`); `kebab-case` for non-component files and route folders; `UPPER_SNAKE_CASE` for constants.

**API:** versioned base `/api/v1`; resources are plural nouns in `kebab-case` (`/api/v1/employees`); JSON payloads use `camelCase` (mapped from backend `snake_case` via schema aliases). Details in the [API Strategy](./05-API-Strategy.md).

**Git:** Conventional Commits (`type(scope): summary`) per [Volume 04](../../Blueprint/Volume-04-Engineering-System/README.md).

---

_See also: [Technology Decisions](./02-Technology-Decisions.md) · [Module Map](./03-Module-Map.md)_
