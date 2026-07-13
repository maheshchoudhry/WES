# AI Work Management & Project Execution Engine (Sprint 07)

Makes the AI organization *perform work*. Connects Founder → Projects → AI
Employees → Execution → Completion. No LLM/AI execution — this is the operational
work engine only. Built on the frozen architecture; AI employees (Sprint 06) are
the assignees and reviewers.

## Domain model

```
Project ──< Milestone
   │     ──< ProjectSprint
   │     ──< WorkItem (task) ──> AIEmployee (assignee, reviewer)
   │                        ──> ProjectSprint / Milestone
   │                        ──< Assignment (history)
   │                        ──< WorkDependency (blocks / related / duplicate)
   │                        ──< Comment
   │                        ──< AttachmentMetadata
   └──< ActivityLog (timeline)
```

Migration `0004_work_management` adds: `projects`, `milestones`, `project_sprints`,
`work_items`, `assignments`, `work_dependencies`, `activity_log`, `comments`,
`attachments_metadata`.

## Statuses & priorities

- **Work status** (Kanban): Backlog · Planned · Assigned · In Progress · Review ·
  Testing · Done (plus Blocked / Archived off-board).
- **Priority**: Critical · High · Medium · Low.
- **Sprint**: Planned · Active · Completed. **Milestone**: Pending · In Progress · Completed.

## Assignment engine

The Founder creates work; the AI Product Manager plans; the Chief Architect
reviews technical tasks; engineers (Backend/Frontend/AI/QA/DevOps/Security AI),
the designer, and the writer receive assignments. Assigning a task records an
`Assignment` row, sets the task's assignee/reviewer, moves a backlog/planned task
to **Assigned**, and writes an activity-timeline entry.

## API endpoints

| Method | Path |
|--------|------|
| GET/POST | `/api/v1/projects`, GET/PATCH/DELETE `/projects/{id}` |
| GET | `/projects/{id}/sprints`, `/projects/{id}/milestones` |
| GET/POST | `/api/v1/sprints` (+ PATCH `/sprints/{id}`), `/api/v1/milestones` |
| GET/POST | `/api/v1/tasks`, GET/PATCH/DELETE `/tasks/{id}` |
| POST | `/tasks/{id}/assign`, `/tasks/{id}/dependencies`, `/tasks/{id}/comments` |
| GET/POST | `/api/v1/assignments` |
| GET | `/api/v1/activity` |
| GET | `/api/v1/work/kanban`, `/work/founder-summary`, `/work/ai-summary` |

Tasks support filtering (project, sprint, status, priority, assignee), search, and pagination.

## RBAC (reuses Sprint 04)

`work:read` → all authenticated roles (view assigned work). `work:write`
(create/update/delete projects, sprints, tasks; assign) → **Founder, Director,
Department Head**. Missing auth → 401, insufficient role → 403.

## Dashboards

- **Founder Dashboard** — total projects, total tasks, blocked, velocity (and
  `founder-summary` provides tasks-by-status, sprint progress, upcoming deadlines,
  AI workload).
- **AI Company Dashboard** — assigned / in-progress / completed work, team
  capacity, work distribution, department load.

## Kanban

`/work/kanban` returns ordered columns (Backlog → Done). The frontend Task Board
renders one column per status; each card carries a status selector that moves the
task (a `PATCH /tasks/{id}` status change) — a drag-and-drop-ready structure.

## Seed data

`PROJECT-001` (WORLD): owned by the AI CEO, 2 milestones, 3 sprints (two completed
with velocity 20/24, one active), 10 sample tasks spread across every Kanban
column, assigned to AI engineers with the Chief Architect as reviewer, a
dependency, a comment, and an activity timeline. Idempotent.

## Frontend

Projects · Project Detail (sprints, milestones, tasks) · Task Board (Kanban) ·
Task Detail (status change + activity) · "Work" navigation section · Founder and
AI dashboard work widgets.
