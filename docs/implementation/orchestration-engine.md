# AI Orchestration Engine & Provider Abstraction (Sprint 09)

Orchestrates AI employees through a **provider-independent** pipeline. WES is not
locked to Claude, OpenAI, Gemini, OpenRouter, or Ollama — business logic talks
only to the Provider Abstraction Layer. The **Mock provider** runs the whole
system with no API keys; enabling a real provider later means adding a key in
Settings — no architecture change.

## Provider Abstraction Layer (`app/providers/`)

Every provider implements one interface (`BaseProvider`):

```
initialize() · health() · execute() · stream() · cancel()
estimate_tokens() · estimate_cost()
```

- `MockProvider` — fully functional, deterministic, key-free (used everywhere).
- `Claude / OpenAI / Gemini / OpenRouter / Ollama` — implement the interface but
  report **unavailable** and refuse to execute until configured (no live SDK/keys
  in this build).
- `ProviderRegistry` maps names → classes; `ProviderFactory.create(name, config)`
  instantiates. Only this layer knows concrete providers.

## Execution pipeline

```
Queue -> Context -> Prompt -> Provider -> Response -> Review -> History -> Next
```

`OrchestrationService.run_stage(employee, work_item, provider?)`:
1. Resolve provider (explicit, else role→provider mapping, else default).
2. `ContextBuilder` assembles project, sprint, task, acceptance criteria,
   repository, employee profile, responsibilities, capabilities, SOP, prompt,
   decision rules, previous messages, and organization context.
3. `PromptBuilder` assembles system/role/SOP/task/history messages (versioned `v1`).
4. Create an `ExecutionRun`; persist prompt messages.
5. `provider.execute()` with retry (`retry_history`).
6. Persist output, assistant message, `execution_metrics`, `token_usage`,
   `cost_tracking`, and a `provider_health` record.
7. `review_run()` records the review outcome (approved / rejected / returned / escalated).

`run_workflow(work_item)` runs a stage for each persisted handoff recipient
(Founder → CEO → PM → Architect → Backend → Frontend → QA → Writer → Founder Review).

## Memory

`MemoryService`: short-term (recent thread messages, fed back into the prompt),
conversation memory (full thread), plus a `LongTermMemory` interface (null impl,
ready for a future vector backend).

## Database changes

Migration `0006_ai_orchestration_engine` (10 tables): `ai_providers`,
`provider_configs`, `conversation_threads`, `execution_runs`, `execution_messages`,
`execution_metrics`, `token_usage`, `cost_tracking`, `provider_health`,
`retry_history`. Role→provider mapping is stored as `provider_configs` rows.

## API endpoints

| Method | Path |
|--------|------|
| GET | `/providers`, `/providers/role-mappings` |
| POST | `/providers/health-check`, `/providers/role-mappings` |
| PATCH/POST | `/providers/{id}/enabled`, `/providers/{id}/default`, `/providers/{id}/config` |
| POST | `/orchestration/run`, `/orchestration/run-workflow` |
| GET | `/orchestration/runs`, `/orchestration/runs/{id}` |
| POST | `/orchestration/runs/{id}/review` |
| GET | `/orchestration/threads/{id}/messages` |
| GET | `/orchestration/founder-dashboard`, `/orchestration/ai-dashboard/{employee_id}` |

## RBAC (reuses Sprint 04)

`orch:read` → all authenticated roles. `orch:write` (run pipeline, provider
settings) → **Founder only** (Director/Chief-Architect/Employees are read-only).

## Dashboards

- **Founder** — provider status/health, running/failed/completed executions, token
  usage, estimated cost, average runtime.
- **AI** — current provider, conversation, context, last prompt/response, memory size.

## Settings

Enable/disable providers, set the default, role→provider mapping, run health
checks, and (masked) API-key placeholders. **No real secrets are stored.**

## Seed data

Six providers (Mock enabled + default; others disabled with placeholder configs),
every AI role mapped to Mock, initial health records, and one sample pipeline run
through the Mock provider (thread + messages + metrics + usage + cost). Idempotent.

## Enabling a real provider later

1. In Settings, set the provider's API key and enable it.
2. Implement `_call()` in that provider's adapter (the only change needed).
Nothing in the orchestration/business layer changes — that is the whole point.
