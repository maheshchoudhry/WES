# Autonomous Software Development Engine (Sprint 13)

The capstone engine: it transforms a software task into a **real** implementation
workflow that combines Repository Intelligence, the Knowledge Engine, the Provider
Platform, and the Execution Engine. Every AI-executed implementation is
**explainable** (plan + rationale + review), **reviewable** (diff + PR), and
**reversible** (isolated git sandbox). The **Founder is the final authority** — the
engine never pushes, never merges, and never touches Blueprint or WORLD.

Verified live: a task produced 3 generated files, **2 real git commits**, **real
pytest execution (2 tests passed)**, an automated review (score 100), and a real
pull-request draft (+49 lines) — then Founder approval without any merge.

## Development architecture

```
Founder → task
  → Plan (Repo Intelligence + Knowledge)  → Repo Analysis → Knowledge
  → Implement (Provider Layer) → Modify (safety-checked) → Test (compile+pytest)
  → Review (7 dimensions) → Document (Knowledge) → Git branch + atomic commits
  → Pull-Request draft → Founder Approval
```

Layered services over the ORM; the workflow records one `development_sessions`
row per stage (the task timeline) and drives the task status machine.

## Implementation workflow

`DevelopmentService.run_workflow(task)`:
1. **Planning** — `PlanningService` assembles affected files, architecture
   context, dependencies, required knowledge/APIs, implementation order, risk
   analysis, and acceptance criteria from Repository Intelligence + Knowledge.
2. **Sandbox + branch** — a fresh, real git repo under the workspace dir; a
   feature branch `feature/auto-<code>`.
3. **Implementation** — `GenerationService` produces file changes through the
   Provider Abstraction Layer (provider-independent). In this build the Mock
   provider drives a deterministic, standards-compliant, **compilable + tested**
   scaffold; a live provider's output becomes the content with no change.
4. **Repository modification** — `RepositoryModificationService` runs mandatory
   **safety checks** (repo context, knowledge, impact analysis, architecture
   verification, path containment) then applies changes and makes **atomic
   Conventional Commits** (feat + docs).
5. **Testing** — `TestingService` runs REAL commands in the sandbox:
   `py_compile` (static), `pytest` (unit), and best-effort `ruff` (lint).
6. **Review** — `ReviewService` scores the change across 7 dimensions
   (architecture, coding standards, security, performance, documentation,
   maintainability, test coverage) with per-finding severity.
7. **Documentation** — `DocumentationService` writes implementation notes into
   the Knowledge Engine (linked to the repository).
8. **Pull request** — `PullRequestService` builds a draft (title, body, diff
   summary, release notes) from real git state. Never pushed, never merged.
9. **Approval** — `ApprovalService` records the Founder's approve/reject/changes;
   approval marks the PR approved but a **human performs the merge**.

## Repository safety

Before every modification: retrieve repository context, retrieve knowledge, run
impact analysis, detect dependencies, verify architecture — and confine all
writes to the sandbox. Paths containing `blueprint`/`world` or escaping the
sandbox are rejected (`SandboxError`). Blueprint and WORLD are never modified.

## Git workflow

Real subprocess `git`: init → feature branch → atomic Conventional Commits →
`git diff` / `--shortstat` / `rev-list`. **Never `push`, never `merge`.** Each
sandbox is a standalone, inspectable, disposable repository.

## Database changes — migration `0010` (10 tables)

`development_tasks`, `development_sessions`, `implementation_plans`,
`generated_changes`, `code_reviews`, `review_comments`, `test_runs`,
`pull_requests`, `approval_history`, `implementation_metrics`.

## API endpoints (`/development`)

| Method | Path |
|--------|------|
| GET/POST | `/tasks`, `/tasks/{id}` |
| POST | `/run` (create + run), `/tasks/{id}/run` |
| GET | `/tasks/{id}/timeline`, `/pending-approvals` |
| POST | `/tasks/{id}/approve` |
| GET | `/founder-dashboard`, `/ai-dashboard` |

## RBAC (reuses Sprint 04)

`dev:read` → all roles (monitor). `dev:execute` (create + run tasks) → Founder +
Director. `dev:approve` (approve/reject PRs) → **Founder only**.

## Dashboards

- **Founder** — running/completed/failed tasks, pending approvals, open PRs,
  recent tasks.
- **AI** — current task, branch, implementation/review/testing status, timeline.

## Frontend

Development Dashboard (launch + overview), Implementation Viewer (plan, metrics,
PR), Repository Changes (syntax-colored diffs), Review Center (7-dimension
findings + test results), Task Timeline (stage-by-stage), Pull Request Center
(drafts + release notes), Approval Center (approve/reject). Plus a founder
dashboard widget and nav.

## Explainable, reviewable, reversible

- **Explainable** — the plan, per-change rationale, and review are stored.
- **Reviewable** — the full diff and PR draft are inspectable before any action.
- **Reversible** — everything lives in an isolated sandbox; discarding it undoes
  the work with zero impact on any real repository.

## Extending in Sprint 14 (no core changes)

The stage machine, `generated_changes`, `code_reviews`, and `test_runs` are the
seams for advanced AI review, security analysis, performance optimization, and
enterprise quality gates — added as new review dimensions / test kinds / stages
without changing the core APIs or data model.
