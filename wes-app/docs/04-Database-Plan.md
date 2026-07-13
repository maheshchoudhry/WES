# High-Level Database Plan

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Frozen (high-level) &nbsp;|&nbsp; **Owner:** WES Engineering

Major entities only. **No detailed schema** in Sprint 01 — columns and constraints are defined per module during implementation.

## Core Entities

| Entity | Purpose |
|--------|---------|
| **User** | An account that can log in (human or system). |
| **Role** | A named set of permissions. |
| **Permission** | A discrete access right. |
| **Employee** | An AI employee profile (links to a role definition). |
| **Department** | An organizational department. |
| **Project** | A managed project (e.g., Project-001: WORLD). |
| **Task** | A unit of work within a project. |
| **Sprint** | A time-boxed iteration of tasks. |
| **Document** | A knowledge-base entry (decision, lesson, practice, doc). |
| **Report** | A generated status/progress report. |
| **AuditLog** | A record of significant actions for traceability. |

## High-Level Relationships

```
User  ──(has)── Role ──(grants)── Permission
Department ──(contains)── Employee
Project ──(contains)── Sprint ──(contains)── Task
Employee ──(owns)── Task
Project ──(produces)── Report
Project/Task ──(produces)── Document
User/Employee ──(acts →)── AuditLog
```

## Principles

- Every table uses a surrogate primary key and created/updated timestamps.
- Access control is modeled as Users → Roles → Permissions (RBAC).
- Schema evolves through Alembic migrations; no manual schema edits.

---

_See also: [Module Map](./03-Module-Map.md) · [API Strategy](./05-API-Strategy.md)_
