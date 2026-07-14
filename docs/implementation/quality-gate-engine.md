# AI Review, Security & Quality Gate Engine (Sprint 14)

The final engineering-validation layer. Every autonomous implementation (Sprint
13) is run through six review engines, aggregated into a **quality gate** with
per-gate scores and findings, scored for risk, checked for compliance, and
assessed for release readiness — **before it can reach Founder approval**. No
implementation is `approval_eligible` until all mandatory gates pass; the Founder
may still explicitly override. **Blueprint frozen. WORLD untouched. No auto-merge.**

Verified live: a clean implementation scored 100 across all engines, passed all 7
gates, produced 0 critical findings, passed all 6 compliance policies, and was
release-ready — while a change containing a hardcoded secret was blocked (security
critical) and required a Founder override.

## Review pipeline

```
Development Completed → Architecture Review → Code Review → Security Scan
  → Performance Analysis → Dependency Analysis → Documentation Validation
  → Test Validation → Quality Gates → Founder Approval
```

The gate runs as a stage in the autonomous workflow (after documentation, before
the pull request) and again on demand via `/quality/tasks/{id}/evaluate`.

## Review engines (`quality_review_engines.py`)

Pure AST/regex analyzers over the real generated code:

- **Architecture** — layer violations, circular dependencies, repository/service
  patterns, API consistency, naming, folder standards.
- **Code** — complexity (branch count), maintainability (length), readability,
  dead/duplicated code, coding standards, error handling, logging.
- **Security** — hardcoded secrets (CWE-798), SQL injection (CWE-89), command
  injection (CWE-78), path traversal (CWE-22), eval/exec.
- **Performance** — nested loops, N+1 / DB calls inside loops.
- **Dependency** — deprecated packages, unused imports, license/health signals.
- **Documentation** — module/function docstrings, technical docs, knowledge-base
  updates.

## Quality gates

Mandatory gates (seeded `quality_rules`, evaluated by `QualityGateService`):
architecture score ≥ 90 · security critical = 0 · performance critical = 0 ·
tests passed = 100% · formatting clean · lint clean · documentation complete.
`approval_eligible` is true only when **all** mandatory gates pass.

## Risk analysis

`quality_metrics`: risk, impact, confidence, complexity, and maintainability
scores derived from finding counts and severities.

## Compliance

`compliance_findings` per policy: no hardcoded secrets, tests present,
Blueprint/WORLD untouched, Conventional Commits, no auto-merge, license
compatible — each pass/warn/fail.

## Release readiness

`release_readiness`: `ready` only when the gate is approval-eligible **and** all
compliance passes; otherwise `blocked` (criticals) or `not_ready`, with the list
of blockers.

## Approval enforcement

`ApprovalService.decide` now refuses to **approve** a task unless a quality gate
has been evaluated; a failing gate requires an explicit `override=true` from the
Founder. Rejection / changes-requested are always allowed.

## Database changes — migration `0011` (10 tables)

`quality_rules`, `quality_gate_runs`, `review_findings`, `security_findings`,
`performance_findings`, `dependency_findings`, `documentation_findings`,
`compliance_findings`, `quality_metrics`, `release_readiness`.

## API endpoints (`/quality`)

| Method | Path |
|--------|------|
| GET | `/rules` |
| POST | `/tasks/{id}/evaluate` |
| GET | `/tasks/{id}/gate`, `/tasks/{id}/report` |
| GET | `/founder-dashboard`, `/ai-dashboard` |

Plus `override` on `POST /development/tasks/{id}/approve`.

## RBAC (reuses Sprint 04)

`quality:read` → all roles (review). `quality:review` (run/re-run gates) →
Founder + Director. Approval override → Founder (`dev:approve`).

## Frontend

Quality Gate Dashboard (aggregate + gate checklist + rules), Review Dashboard
(architecture + code + documentation findings), Security Dashboard (findings +
compliance), Performance Dashboard (performance + dependency findings), Release
Readiness Dashboard (status + blockers + checklist), Risk Analysis Dashboard
(risk profile bars). Plus a founder-dashboard widget and nav.

## Extending in Sprint 15 (no core changes)

The engine list, gate rules, and finding tables are the seams for CI/CD,
deployment automation, production monitoring, rollback, and release pipelines —
add new engines / rules / finding kinds without changing the existing APIs or
data model.
