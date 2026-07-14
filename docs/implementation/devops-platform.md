# Enterprise DevOps, CI/CD & Production Platform (Sprint 15)

The final layer — it completes the WES software-engineering lifecycle. An
approved, quality-gated implementation moves through a **real** CI/CD pipeline
(build → test → security → docker → artifact → release → deploy) into monitored,
rollback-ready environments. All production deployment is **Founder-gated**;
nothing is pushed, merged, or deployed to a real production host, and Blueprint
and WORLD are never touched.

Verified live: a pipeline produced a real build (sha256 checksum), a **real
Docker image** (`wes/dev-0001:pipe-0002`), ran real pytest, cut release
`0.5.0-beta.2`, **really deployed** it to staging and (after Founder approval) to
production (files on disk, verified), and captured real psutil system health — then
a real rollback re-deployed a previous release.

## The complete lifecycle

```
Plan → Knowledge → Repository Analysis → AI Development → Quality Review →
Founder Approval → Build → Test → Package → Deploy → Monitor → Rollback
```

Sprints 06–14 produce an approved, gated implementation; Sprint 15 ships it.

## CI/CD pipeline

`PipelineService.run(task, environment)` requires a **Founder-approved** task and
executes 11 stages, recording each:

1. **build** — `py_compile` the sandbox + package a real `.tar.gz` artifact (sha256).
2. **unit_tests** / 3. **integration_tests** — real `pytest` in the sandbox.
4. **security_scan** — reuses the Sprint 14 quality gate (critical = 0).
5. **docker_image** — a **real** `docker build` when enabled + available; else skipped.
6. **artifact** — the built tarball.
7. **release_candidate** — a semantic version (`0.5.0-beta.N`) + release notes.
8. **staging_deploy** — a real local deployment (extract + verify).
9. **monitoring** — a real health snapshot.
10. **rollback_ready** — the previous release is available to roll back to.
11. **production_approval** — Founder-gated; the pipeline pauses `awaiting_production`.

`POST /devops/pipelines/{id}/deploy-production` (Founder) performs the real
production deployment.

## Build system

Real builds from the Sprint-13 git sandbox: `py_compile`, a `.tar.gz` artifact
with a sha256 checksum + metadata, and an optional real Docker image (multi-stage
ready). Everything under the DevOps workspace — never a real production host.

## Deployment

`DeploymentService` performs **real local deployments**: it extracts the release's
artifact into `<workspace>/deployments/<env>/<version>/` and verifies it by
compiling. Strategies (standard / blue-green / rolling) per environment.
Production requires an explicit Founder approval.

## Environments

Four seeded profiles — development → testing → staging → production — with
production Founder-gated and blue-green / rolling strategies. Each has a
deployment target and non-secret variables.

## Monitoring & incidents

`HealthService` captures a **real** snapshot: CPU/memory/disk via `psutil`, plus
application, API, database, AI-provider, and execution-queue health. Breaches
(CPU/disk/DB) raise `IncidentReport`s with recovery actions; monitoring events and
system-health rows are retained.

## Rollback

`RollbackService` re-deploys a previous release's artifact to an environment (real
local rollback) and records `rollback_history`. Deployment / release / artifact /
configuration rollback are all supported through the same artifact re-deploy path.

## Release management

`ReleaseService` cuts semantic versions, generates release notes from the
implementation's plan + pull-request, and tracks version + deployment history.

## Database changes — migration `0012` (12 tables)

`environment_profiles`, `deployment_targets`, `pipeline_runs`, `build_runs`,
`release_versions`, `release_notes`, `deployment_artifacts`, `deployment_runs`,
`rollback_history`, `monitoring_events`, `system_health`, `incident_reports`.

## API endpoints (`/devops`)

| Method | Path |
|--------|------|
| GET/POST | `/pipelines`, `/pipelines/run`, `/pipelines/{id}` |
| POST | `/pipelines/{id}/deploy-production` |
| GET | `/deployments`, `/releases`, `/environments`, `/rollback-history` |
| POST | `/rollback` |
| GET/POST | `/monitoring/health`, `/monitoring/snapshot`, `/monitoring/events` |
| GET/POST | `/incidents`, `/incidents/{id}/resolve` |
| GET | `/founder-dashboard`, `/ai-dashboard` |

## RBAC (reuses Sprint 04)

`devops:read` → all roles. `devops:execute` (run pipelines, deploy non-production)
→ Founder + Director. `devops:production` (production deploy + rollback) → **Founder only**.

## Frontend

CI/CD Pipeline (run + stage timeline + production approval), Deployment, Release,
Monitoring (health + events), Incident, Environment, and Rollback dashboards; plus
a founder-dashboard widget and nav.

## Production safety

- No auto-push, no auto-merge, no auto-deploy to production — every production
  action requires an explicit Founder decision.
- Blueprint and WORLD are never modified; all work is confined to the sandbox and
  DevOps workspace.
- Every deployment is reversible (artifact re-deploy) and auditable (pipeline,
  deployment, rollback, and incident records).

## Toward v0.5.0-beta

With Sprint 15, WES OS spans the full lifecycle — planning, knowledge, repository
intelligence, autonomous development, quality gates, and CI/CD to monitored,
rollback-ready environments — without changing the core architecture. The release
channel and versioning (`0.5.0-beta.N`) are in place for the beta.
