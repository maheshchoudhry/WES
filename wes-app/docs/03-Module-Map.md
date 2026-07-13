# Module Map

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Frozen &nbsp;|&nbsp; **Owner:** WES Engineering

Initial application modules. Each is a vertical slice (backend router → service → repository; frontend feature folder). Modules are **defined, not implemented** in Sprint 01. They mirror the company structure so the app becomes the operating system of WES.

| Module | Purpose | Maps To |
|--------|---------|---------|
| **Authentication** | Login, sessions, tokens, access control. | Users, Roles, Permissions |
| **Dashboard** | At-a-glance company and project status. | Cross-module |
| **Company** | Company profile, policies, org overview. | [Company](../../Company/README.md) |
| **Departments** | Manage departments and their data. | [Departments](../../Departments/README.md) |
| **Employees** | AI employee profiles, status, assignments. | [Employees](../../Employees/README.md) + [EOS](../../Company/Employee-Operating-System/README.md) |
| **Projects** | Project profiles and lifecycle. | [Projects](../../Projects/README.md) + [POS](../../Projects/Project-Operating-System/README.md) |
| **Tasks** | Task creation, assignment, status, sprints. | [Task Management](../../Projects/Project-Operating-System/Task-Management-Framework.md) |
| **Reports** | Daily, weekly, milestone, project reports. | [Reporting System](../../Company/Communication-System/Reporting-System.md) |
| **Knowledge Base** | Decisions, lessons, best practices, docs. | [CMS](../../Company/Company-Memory-System/README.md) |
| **Settings** | User and system configuration. | System |

## Module Dependencies (high-level)

- **Authentication** underpins every other module.
- **Dashboard** and **Reports** read across modules.
- **Employees**, **Departments**, **Projects**, **Tasks** form the operational core.
- **Knowledge Base** captures output from Projects and Tasks.

---

_See also: [Architecture](./01-Architecture.md) · [Database Plan](./04-Database-Plan.md)_
