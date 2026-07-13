# Technology Decisions

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Frozen &nbsp;|&nbsp; **Owner:** WES Engineering

The finalized stack. Choices align with [Volume 06 — Technology Stack](../../Blueprint/Volume-06-Technology-Stack/README.md) (TypeScript for web, Python for backend/AI, PostgreSQL, Git/GitHub) and favor production maturity and long-term scalability.

| Concern | Decision | Why |
|---------|----------|-----|
| **Frontend Framework** | Next.js (React + TypeScript), App Router | Mature, scalable React framework with routing, SSR/SSG, and strong tooling. TypeScript gives type safety across a growing app. Matches the Blueprint's web stack. |
| **Backend Framework** | FastAPI (Python) | High-performance async API framework with first-class validation (Pydantic) and OpenAPI. Python is the Blueprint's backend/AI language, so future AI features integrate natively. |
| **Database** | PostgreSQL (via SQLAlchemy ORM + Alembic) | Reliable, standard relational database (Blueprint default). SQLAlchemy for a clean data layer; Alembic for versioned migrations. |
| **Authentication** | JWT (OAuth2 password flow), hashed passwords (passlib) | Stateless, scalable auth that fits a decoupled API. OAuth2/JWT is standard and extensible to SSO later. |
| **API Design Style** | REST, versioned (`/api/v1`), JSON | Simple, well-understood, and cache/tooling friendly. Versioning protects clients as the API evolves. GraphQL considered but rejected as unnecessary complexity for v1. |
| **State Management** | TanStack Query (server state) + Zustand (client state) | Separates server cache from UI state. Less boilerplate than Redux while scaling cleanly. |
| **Styling Framework** | Tailwind CSS | Utility-first, consistent, fast to build with, and easy to standardize across modules. |
| **Testing Framework** | Backend: pytest + httpx; Frontend: Vitest + React Testing Library; E2E: Playwright | Production-standard tools per layer, satisfying the testing strategy in [Volume 08](../../Blueprint/Volume-08-Security-Quality/README.md). |
| **Deployment Strategy** | Docker containers, orchestrated via docker-compose locally; CI/CD via GitHub Actions | Reproducible environments and a clean path to cloud hosting. Containers keep frontend, backend, and database consistent across environments. |

## Rejected / Deferred

- **NestJS backend** — rejected to keep the backend in Python for native AI integration.
- **GraphQL** — deferred; REST is sufficient for v1 and simpler to secure and cache.
- **Kubernetes** — deferred; docker-compose is enough until scale demands orchestration ([Volume 10](../../Blueprint/Volume-10-Automation/README.md)).

---

_See also: [Architecture](./01-Architecture.md) · [API Strategy](./05-API-Strategy.md)_
