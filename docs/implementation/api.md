# Company Engine — API Reference

Base path: `/api/v1`. All request and response bodies are JSON.

## Response envelope

Success:
```json
{ "data": { }, "meta": { "total": 1 } }
```
Error:
```json
{ "error": { "code": "CONFLICT", "message": "…", "details": [] } }
```

| HTTP | `code` | When |
|------|--------|------|
| 404 | `NOT_FOUND` | Entity does not exist |
| 409 | `CONFLICT` | Duplicate, or entity is in use |
| 422 | `VALIDATION_ERROR` | Field validation or bad business reference |

Pagination via `?page=<n>&page_size=<n>` (default `page=1`, `page_size=50`).

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness |
| GET | `/health/ready` | Readiness (checks DB connectivity) |

## Companies

| Method | Path | Description | Success |
|--------|------|-------------|---------|
| GET | `/companies` | List companies | 200 |
| POST | `/companies` | Create a company | 201 |
| GET | `/companies/{id}` | Get a company | 200 |
| PATCH | `/companies/{id}` | Update a company | 200 |
| DELETE | `/companies/{id}` | Delete a company | 204 |

Create body:
```json
{ "name": "WORLD Engineering Studio", "slug": "wes",
  "company_type": "Independent AI Engineering Company", "purpose": "…" }
```

## Departments

| Method | Path | Description | Success |
|--------|------|-------------|---------|
| GET | `/departments?company_id={id}` | List (optionally by company) | 200 |
| POST | `/departments` | Create a department | 201 |
| GET | `/departments/{id}` | Get a department | 200 |
| PATCH | `/departments/{id}` | Update a department | 200 |
| DELETE | `/departments/{id}` | Delete a department | 204 |

Create body:
```json
{ "company_id": "<uuid>", "code": "DEPT-02", "name": "Engineering", "focus": "…" }
```

## Employees

| Method | Path | Description | Success |
|--------|------|-------------|---------|
| GET | `/employees?company_id={id}&department_id={id}` | List (optional filters) | 200 |
| POST | `/employees` | Register an employee | 201 |
| GET | `/employees/{id}` | Get an employee | 200 |
| PATCH | `/employees/{id}` | Update an employee | 200 |
| PUT | `/employees/{id}/department` | Assign / clear department | 200 |
| DELETE | `/employees/{id}` | Delete an employee | 204 |

Register body:
```json
{ "company_id": "<uuid>", "department_id": "<uuid|null>",
  "reports_to_id": "<uuid|null>", "employee_code": "WES-EMP-006",
  "full_name": "Backend Engineer", "email": "wes-emp-006@wes.studio",
  "position": "Backend Engineer", "authority": "operational", "status": "active" }
```

Assign department body:
```json
{ "department_id": "<uuid|null>" }
```

## Dashboard (read-only aggregation — Sprint 03)

All `GET`, under `/api/v1/dashboard`. Composed from Company Engine data; no new tables.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/company-summary` | Company + department/employee counts |
| GET | `/dashboard/stats` | Totals and breakdowns (by status, by authority) |
| GET | `/dashboard/departments` | Per-department employee counts |
| GET | `/dashboard/employees` | Employee directory (resolved department & manager) |
| GET | `/dashboard/activity?limit=N` | Recent activity (default 10, max 50) |
| GET | `/dashboard/health` | API + database health and entity counts |

Interactive OpenAPI docs are served at `/docs` when the backend is running.
