# WES Frontend

Next.js (React + TypeScript) frontend for the WES Web Application. Architecture is frozen in [../docs/01-Architecture.md](../docs/01-Architecture.md).

## Requirements

- Node.js 20+

## Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

The app runs at `http://localhost:3000` and expects the backend API at `NEXT_PUBLIC_API_BASE_URL`.

## Structure (`src/`)

| Folder | Purpose |
|--------|---------|
| `app/` | Next.js App Router routes and layouts. |
| `features/` | Domain modules (auth, employees, projects, …). |
| `components/` | Shared, reusable UI components. |
| `lib/` | API client and utilities. |
| `hooks/` | Shared React hooks. |
| `stores/` | Client state (Zustand). |
| `types/` | Shared TypeScript types. |
| `styles/` | Global styles. |

> Sprint 01 provides the shell only. Modules are implemented in later sprints per the [roadmap](../docs/06-Development-Roadmap.md).
