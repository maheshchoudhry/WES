# AI Company Core (Sprint 06)

Transforms WES OS from a software application into an **AI software company**. AI
employees are first-class entities with hierarchy, responsibilities, capabilities,
KPIs, and a reporting structure — an AI organization that can manage software
development. Built on the frozen Company Engine architecture and Sprint 04 RBAC.

## Domain model

```
AIDepartment (Executive, Product, Engineering)
AIRole (12 roles, with level + is_executive_head)
AICapability (reusable catalog)  ──many-to-many──┐
                                                  │
AIEmployee ──department──> AIDepartment           │
   │  ├─ role ──> AIRole                           │
   │  ├─ manager ──> AIEmployee (self-ref)  ◄──────┘ capabilities
   │  ├─ responsibilities ──> AIResponsibility (1:M)
   │  └─ kpis ──> AIKPI (1:M)
```

Migration `0003_ai_company_core` adds: `ai_departments`, `ai_roles`,
`ai_capabilities`, `ai_employees`, `ai_responsibilities`, `ai_kpis`, and the
`ai_employee_capabilities` association. AI Reporting is derived from
`manager_id`; AI Status is the `status` enum. The Company Engine schema is
unchanged.

## AI Employee profile

Employee ID · Name · Department · Role · Manager · Responsibilities · Authority ·
Capabilities · Decision Scope · Status · Version · Created / Updated.

## Organization

| Department | Members |
|-----------|---------|
| Executive | AI CEO, AI CTO, Chief Software Architect |
| Product | AI Product Manager |
| Engineering | Backend, Frontend, AI, QA, DevOps, Security Engineers; UI/UX Designer; Technical Writer |

Reporting: CEO → (CTO → Chief Architect → engineers), (Product Manager →
designer, writer). 12 AI employees, seeded automatically.

## Business rules

- Employee IDs unique; role and department required.
- A reporting manager is required for everyone **except** the CEO
  (`is_executive_head`).
- An employee cannot report to itself.
- **Soft delete only** — `DELETE` sets `is_deleted=true` + `status=archived`,
  hides the row from listings, and promotes direct reports to the deleted
  employee's manager. Rows are never physically removed.
- `version` increments on every update.

## API

| Method | Path | Permission |
|--------|------|-----------|
| GET | `/api/v1/ai-employees` (filter: department_id, role_id, status, search; paginated) | ai:read |
| POST | `/api/v1/ai-employees` | ai:manage |
| GET | `/api/v1/ai-employees/{id}` | ai:read |
| PATCH | `/api/v1/ai-employees/{id}` | ai:update |
| DELETE | `/api/v1/ai-employees/{id}` (soft) | ai:manage |
| GET | `/api/v1/ai-roles` | ai:read |
| GET | `/api/v1/ai-departments` | ai:read |
| GET | `/api/v1/ai-org/chart` · `/departments` · `/summary` | ai:read |

## Authorization (reuses Sprint 04 RBAC)

| Role | AI access |
|------|-----------|
| Founder | Full (read + create + update + delete) |
| Director | Read + Update |
| Department Head | Read + Update |
| Employee | Read |
| Read Only | Read |

`ai:read` → all roles; `ai:update` → founder/director/department_head;
`ai:manage` (create/delete) → founder only. Missing auth → 401, insufficient role → 403.

## Frontend

- **AI Company Dashboard** (`/ai`) — summary stats, org health, department cards.
- **AI Employee Directory** (`/ai/directory`) — searchable/filterable table.
- **AI Employee Profile** (`/ai/employees/:id`) — full profile with responsibilities, capabilities, KPIs.
- **AI Organization Chart** (`/ai/org`) — reporting-hierarchy tree.
- **AI Department View** (`/ai/departments`) — employees grouped by department.
- **Founder Dashboard** — new AI Organization summary (employees, departments, roles, health).
