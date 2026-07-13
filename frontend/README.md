# WES Company Engine — Frontend

Production UI for the **WES Core Company Engine** (Sprint 02): Company Overview,
Department Management, and Employee Management, connected to the backend REST API.

Stack (frozen in Sprint 01 — Blueprint Vol. 06): **TypeScript · React 18 · Vite ·
React Router**. Tests use **Vitest + React Testing Library**.

## Structure

```
src/
  api/          typed API client + per-resource modules (companies, departments, employees)
  components/   Layout, Modal, StatusBadge, state views
  hooks/        useAsync (load/reload/error)
  pages/        CompanyOverview, DepartmentsPage, EmployeesPage
  types.ts      shared domain types (mirror backend schemas)
  __tests__/    component + client tests
```

Every page loads live data from the API and performs real create/read/update/delete
operations — there are no placeholder screens.

## Local development

Requires Node.js 20+.

```bash
cd frontend
npm install
cp .env.example .env
npm run dev        # http://localhost:5173  (/api proxied to http://localhost:8000)
```

Point the app at a backend either via the dev proxy (default) or by setting
`VITE_API_BASE_URL` in `.env`.

## Commands

```bash
npm run dev         # start the dev server
npm run build       # type-check + production build to dist/
npm run typecheck   # tsc --noEmit
npm run test        # run the Vitest suite (9 tests)
```
