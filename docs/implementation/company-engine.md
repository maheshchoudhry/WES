# Company Engine — Architecture & Domain

The Company Engine is the first production module of WES OS. It manages the core
organizational entities that every future module builds on: **Company**,
**Department**, and **Employee**.

## Layered architecture

```
HTTP  →  API routers  →  Services  →  Repositories  →  ORM models  →  Database
                 (Pydantic schemas validate at the boundary)
```

- **API** (`app/api/v1`) — FastAPI routers; translate HTTP to service calls and
  wrap results in the standard envelope.
- **Services** (`app/services`) — business rules, validation, cross-entity
  integrity, orchestration. Raise domain exceptions, never HTTP.
- **Repositories** (`app/repositories`) — all database queries for one aggregate.
- **Models** (`app/models`) — SQLAlchemy 2.0 ORM tables with a portable `GUID`
  type (native UUID on PostgreSQL, `CHAR(36)` on SQLite).
- **Schemas** (`app/schemas`) — Pydantic v2 request/response contracts with field
  validation.

Each request is a single transaction: the `get_db` dependency commits on success
and rolls back on error.

## Domain model

```
Company (1) ──< Department (N)
   │                  │
   └──< Employee (N) ─┘   (Employee.department_id, nullable)
              │
              └──< reports_to (self-reference, nullable)
```

### Company
Root of the organization.

| Field | Notes |
|-------|-------|
| `id` | UUID, generated |
| `name` | unique |
| `slug` | unique, lowercase-hyphenated |
| `company_type` | required |
| `purpose`, `description` | optional |
| `status` | `active` \| `inactive` \| `archived` |

### Department
Belongs to exactly one company.

| Field | Notes |
|-------|-------|
| `company_id` | FK → companies (cascade delete) |
| `code` | unique **within a company** |
| `name` | unique **within a company** |
| `focus` | optional |
| `status` | entity status |

### Employee
Belongs to a company; optionally assigned to a department; may report to another
employee.

| Field | Notes |
|-------|-------|
| `company_id` | FK → companies (cascade delete) |
| `department_id` | FK → departments, nullable (set null on department delete) |
| `reports_to_id` | FK → employees, nullable (self-reference) |
| `employee_code` | globally unique |
| `email` | globally unique, validated |
| `position` | required |
| `authority` | `executive` \| `lead` \| `operational` |
| `status` | `onboarding` \| `active` \| `inactive` \| `archived` |

## Business rules

- A department can only be created for an **existing** company.
- Department `code` and `name` are **unique within their company**.
- Employee `employee_code` and `email` are **globally unique**.
- An employee's department (on register or assignment) must belong to the
  employee's **own company** — cross-company assignment is rejected.
- An employee **cannot report to themselves**.
- A company with departments **cannot be deleted** (remove departments first).
- A department with employees **cannot be deleted** (reassign employees first).

Violations surface as `409 CONFLICT` (duplicates / in-use) or
`422 VALIDATION_ERROR` (bad references / field validation).

## Seed data

`python -m app.db.seed` populates the real WES organization as recorded in the
Company directories: **1 company, 6 departments, 13 employees** with their
reporting hierarchy. The seed is idempotent.
