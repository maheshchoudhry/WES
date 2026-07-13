# Volume 06 — Technology Stack

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Draft &nbsp;|&nbsp; **Owner:** WES &nbsp;|&nbsp; **Project:** WES Blueprint

The technology ecosystem of WORLD Engineering Studio (WES). These are baseline studio-wide choices; individual projects may extend them when justified. Each entry states briefly *why* it exists in WES. Engineering practices that use this stack are in [Volume 04 — Engineering System](../Volume-04-Engineering-System/README.md).

> **Note:** This is a v1.0 baseline. Selections are intentionally common and low-risk so the studio can start building immediately and adjust per project.

---

## Core Technologies

| Technology | Why it exists in WES |
|------------|----------------------|
| **Python** | Primary language for AI, automation, and backend logic — broad ecosystem and fast iteration. |
| **JavaScript / TypeScript** | Standard for web frontends and tooling; TypeScript adds safety at scale. |
| **Markdown** | Default format for all documentation and the Blueprint — portable and GitHub-friendly. |

## Development Tools

| Tool | Why it exists in WES |
|------|----------------------|
| **VS Code** | Standard editor; consistent experience across roles. |
| **Node.js** | Runtime for frontend tooling and JavaScript services. |
| **Formatter / Linter** (e.g., Prettier, Black, ESLint) | Enforce Development Standards automatically. |

## AI Platforms

| Platform | Why it exists in WES |
|----------|----------------------|
| **LLM provider APIs** (e.g., Anthropic Claude / OpenAI) | Power AI Employees and product AI features. |
| **Prompt & agent tooling** | Build, test, and run AI Employee workflows (framework in [Volume 05 — AI System](../Volume-05-AI-System/README.md)). |

## Version Control

| Tool | Why it exists in WES |
|------|----------------------|
| **Git** | Foundation of the engineering workflow — traceable, reviewable history. |
| **GitHub** | Hosting, Pull Requests, and reviews per [Volume 04 — Engineering System](../Volume-04-Engineering-System/README.md). |

## Database

| Technology | Why it exists in WES |
|------------|----------------------|
| **PostgreSQL** | Default relational database — reliable, standard, and well-supported. |
| **SQLite** | Lightweight option for prototypes and local development. |

## Development Environment

- Local development on VS Code with project-defined dependencies.
- Environment configuration via environment variables (no secrets in code).
- Consistent tooling (formatter, linter) shared across projects.

## Infrastructure Overview

- **Source of truth:** GitHub repositories (one per project; WES and WORLD are independent).
- **Compute/hosting:** cloud-based, chosen per project's needs.
- **Automation:** CI/CD to be defined in [Volume 10 — Automation](../Volume-10-Automation/README.md).
- Kept intentionally minimal at v1.0; expands as projects require.

## Future Technology Expansion

Candidates to evaluate as WES grows: containerization (Docker), a dedicated CI/CD platform, vector databases for AI retrieval, monitoring/observability tooling, and a managed cloud provider. Adopted only when a project justifies the added complexity.

---

## Placeholders (Future Expansion)

- Per-project stack profiles
- Approved-library and dependency policy
- Hosting and deployment architecture
- Observability and monitoring stack

---

**Related:** [Volume 04 — Engineering System](../Volume-04-Engineering-System/README.md) · [Volume 05 — AI System](../Volume-05-AI-System/README.md) · [Blueprint Index](../README.md)
