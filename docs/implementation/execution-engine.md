# AI Execution Engine (Sprint 08)

Turns AI employees from organizational entities into **executable software
workers**. No LLM/AI execution — this is the operational execution framework:
workspaces, execution queue, prompt/SOP libraries, decision rules, review queue,
handoffs, execution history, and performance metrics. Built on the AI Company
Core (Sprint 06) and Work Management (Sprint 07).

## Domain model

```
AIWorkspace (1 per AI employee)
ExecutionQueueItem ──> AIEmployee, WorkItem, SOP, PromptTemplate
ExecutionHistory   ──> AIEmployee, WorkItem, ExecutionQueueItem
ReviewItem         ──> reviewer / submitter AIEmployee, WorkItem, ExecutionHistory
Handoff            ──> from / to AIEmployee, WorkItem (sequence = workflow chain)
DecisionRule       ──> AIRole (approval / escalation / review / authority_limit)
PromptTemplate     (system | role | task | review | escalation)
SOP                (coding | review | testing | deployment | documentation | security)
ExecutionContext   ──> AIEmployee, WorkItem (key/value context)
```

Migration `0005_ai_execution_engine` adds all nine tables. Company Engine, AI
Company, and Work Management schemas are unchanged.

## Workflow (persisted handoffs)

```
Founder → AI CEO → AI Product Manager → Chief Architect →
Backend Engineer → Frontend Engineer → QA Engineer → Technical Writer → Founder Review
```

Every handoff is a persisted `Handoff` row with `sequence`, `stage`, `from`/`to`,
and status (pending → accepted → completed). The seed creates the full chain for
PROJECT-001's dashboard task.

## Workspace

`GET /workspaces/{ai_employee_id}` aggregates, per employee: assigned tasks,
execution queue, inbox (pending handoffs), review queue, execution history,
context items, KPIs, and performance (queued / in-progress / completed /
pending-reviews / avg duration).

## Execution queue

Items advance `queued → in_progress → completed` (`POST /execution-queue/{id}/advance`).
Completing an item writes an `ExecutionHistory` record with a computed duration.

## API endpoints

| Method | Path |
|--------|------|
| GET | `/workspaces/{employee_id}` |
| GET/POST | `/execution-queue`, POST `/execution-queue/{id}/advance` |
| GET | `/execution-history` |
| GET/POST | `/reviews`, POST `/reviews/{id}/decision` |
| GET | `/handoffs`, POST `/handoffs/{id}/advance` |
| GET/GET/POST | `/prompts`, `/prompts/{id}`, POST `/prompts` |
| GET/GET/POST | `/sops`, `/sops/{id}`, POST `/sops` |
| GET | `/decision-rules` |
| GET | `/execution/founder-dashboard`, `/execution/ai-dashboard` |

## RBAC (reuses Sprint 04)

`exec:read` → all authenticated roles; `exec:write` (queue advance, reviews,
handoffs, library authoring) → Founder, Director, Department Head. 401 / 403 as
elsewhere.

## Dashboards

- **Founder Dashboard** — AI Execution summary (work queue, in progress, pending
  reviews, completed); `founder-dashboard` also returns avg completion and org
  performance.
- **AI Company Dashboard** — Execution summary (queue, current work, review queue).

## Seed data

Workspaces for all 12 AI employees; 5 prompts (one per type); 6 SOPs (one per
category); decision rules per role; a 5-item execution queue (with history for
completed items); a pending review (Chief Architect ← Backend); the 8-step
handoff workflow chain; and execution context for the Backend engineer. Idempotent.

## Frontend

AI Workspace (per-employee aggregate), Execution Queue (advance), Review Queue
(approve / request changes), Prompt Library, SOP Library, Execution History, and
a Performance Dashboard; new "Execution" navigation section.
