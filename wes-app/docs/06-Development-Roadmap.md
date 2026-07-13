# Development Roadmap

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Frozen &nbsp;|&nbsp; **Owner:** WES Engineering

Implementation is broken into focused sprints. Each sprint delivers one module end to end (backend slice + frontend feature + tests) per the [Definition of Done](../../Blueprint/Volume-04-Engineering-System/README.md).

| Sprint | Focus | Scope |
|--------|-------|-------|
| **01** | Architecture Foundation | Architecture frozen, stack finalized, repo prepared. **(this sprint — complete)** |
| **02** | Authentication | Users, roles, permissions, login, JWT, protected routes. |
| **03** | Dashboard | App shell, navigation, layout, cross-module summary view. |
| **04** | Departments | Department CRUD and directory. |
| **05** | Employees | Employee profiles, status, EOS fields, assignments. |
| **06** | Projects | Project profiles and lifecycle (POS). |
| **07** | Tasks | Tasks, sprints, statuses, dependencies. |
| **08** | Knowledge Base | Decisions, lessons, best practices, documents (CMS). |
| **09** | Reports | Daily, weekly, milestone, project reports. |
| **10** | MVP Integration | Wire modules together, end-to-end flows, hardening. |

## Sequencing Rationale

Authentication first (everything depends on it), then the Dashboard shell to host modules, then the operational core (Departments → Employees → Projects → Tasks) in dependency order, followed by Knowledge Base and Reports which read from that core, and finally MVP integration.

---

_See also: [Architecture](./01-Architecture.md) · [Module Map](./03-Module-Map.md)_
