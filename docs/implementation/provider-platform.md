# Live AI Provider Integration Platform (Sprint 11)

Turns the Sprint 09 Provider Abstraction Layer into a production-ready platform
that executes through **real** external AI providers — while preserving complete
provider independence. Business logic never learns which provider runs; only the
Provider Layer speaks to external APIs. Enabling a provider is a Settings action:
enter an API key and WES executes through it, no architecture change.

> **No keys in source, no plaintext secrets.** Live green connections require the
> founder's own API keys entered in Settings; the Mock provider is always live.

## Provider architecture

```
Execution Engine → Knowledge Retrieval → Context → Prompt
   → Budget gate → Provider (failover chain, retry/backoff) → Streaming
   → Review → History  ── metrics: usage · cost · latency · errors · events
```

- **Common interface** (`BaseProvider`): `initialize/health/test_connection/execute/stream/cancel/estimate_*`.
- **Real adapters** (`app/providers/external.py`) — all via `httpx`, behind the interface:
  - **Claude** → `POST /v1/messages` (`x-api-key`, `anthropic-version`)
  - **OpenAI** / **OpenRouter** → `POST /v1/chat/completions` (`Bearer`)
  - **Gemini** → `POST /v1beta/models/{model}:generateContent?key=…`
  - **Ollama** (local, no key) → `POST /api/chat`
  - **Mock** — always available, deterministic
- **Registry + Factory** — the only place that knows concrete providers.
- **Manager / Router / Failover / Health Monitor / Metrics / Cost Engine** — platform services above the layer; none call external APIs directly.

Each adapter builds its own request and parses its own response; a shared HTTP
helper (`providers/http.py`) centralizes timeouts, error normalization
(HTTP → `ProviderError`, 429 → `RateLimitError`), and SSE parsing. Tests inject an
`httpx.MockTransport` to exercise the **real** request/response code without keys.

## Security design (secret management)

- **Encrypted at rest** — `app/core/secrets.py` `SecretBox`: Fernet (AES-128-CBC +
  HMAC-SHA256) keyed from `WES_SECRET_KEY`, with a stdlib authenticated-cipher
  fallback so the app runs without `cryptography`.
- **`provider_secrets`** stores ciphertext only, scoped to an **environment
  profile** (development/staging/production). Rotation-ready (`last_rotated_at`).
- **Never exposed** — the API returns only a masked hint (`••••••1234`); plaintext
  is decrypted solely by `SecretService` and handed to the Provider Layer at
  execution time. Verified: the raw key never appears in any response.
- **Audited** — every enable/disable/default/secret/model/failover/connection
  change writes a `provider_events` row (actor + detail).

## Execution flow

`run_stage` resolves the provider (explicit, else role→provider mapping, else
default), retrieves knowledge, builds the prompt, then:

1. **Budget gate** — estimate tokens/cost; if a hard-stop limit would be breached,
   refuse **before contacting any provider**, notify the founder.
2. **Failover chain** — primary first, then other enabled providers by priority.
   (An explicitly-requested provider is honored strictly — no silent failover.)
3. **Retry/backoff** — `RateLimitError` (429) backs off exponentially and retries
   the same provider; other errors fail over to the next in the chain.
4. On success, persist output, metrics, token usage, dimensioned `provider_usage`
   + billing rollup, and latency; a failover records an event and notifies the founder.

## Streaming flow

`POST /orchestration/stream` returns Server-Sent Events: `start` → `token`* →
`done`/`error`. The provider's `stream()` yields partial tokens (real SSE for live
providers; word-by-word for Mock). Cancellation via
`POST /orchestration/runs/{id}/cancel` (checked between tokens). Verified live.

## Budget system

Founder-configured `budget_configs` (global): daily/monthly cost limits, per-run
max cost/tokens, warning threshold, and hard-stop. `BudgetService.check` runs
pre-execution; `status()` reports spend vs limits with warning/exceeded flags.

## Failover design

`FailoverService.chain(primary)` = primary, then enabled providers ascending by
`priority` (Mock seeded at priority 10 as the always-healthy fallback). On primary
failure the run continues on the next provider and the founder is notified.

## Database changes — migration `0008`

`ai_providers` gains `active_model` + `priority`. New tables: `provider_secrets`,
`provider_models`, `provider_usage`, `provider_billing`, `provider_latency`,
`provider_errors`, `provider_events`, `budget_configs`.

## API endpoints (added)

| Method | Path |
|--------|------|
| POST | `/providers/{id}/secret`, `/providers/{id}/test` |
| GET/POST | `/providers/{id}/models`; POST `/providers/{id}/active-model`, `/providers/{id}/priority` |
| GET | `/providers/dashboard`, `/providers/ai-dashboard/{id}`, `/providers/metrics`, `/providers/events`, `/providers/cost` |
| GET/PUT | `/providers/budget` |
| POST | `/providers/monitor` |
| POST | `/orchestration/stream` (SSE), `/orchestration/runs/{id}/cancel` |

## Cost management

Per-execution `provider_usage` is dimensioned by provider / AI employee / project
/ day / month, with a `provider_billing` rollup. `/providers/cost?group_by=` and
the dashboards aggregate prompt/completion/total tokens and estimated cost.

## Model management

`provider_models` holds selectable models with per-model pricing and context
windows (Claude Opus/Sonnet, GPT-4o/GPT-4.1/GPT-5-ready, Gemini Pro, Llama, …). The
active model is selectable per provider; the data model supports future models.

## Rate limiting

429 responses become `RateLimitError` (honoring `Retry-After`); the execution
layer retries with exponential backoff, then fails over. Errors and rate-limit
events are recorded to `provider_errors` / `provider_events`.

## RBAC (reuses Sprint 04)

`orch:read` → all roles (dashboards, budget, metrics, events). `orch:write` →
**Founder only** (secrets, enable/default, models, priority, budget, run, stream).

## Enabling a real provider in production

1. In Settings, enter the provider's API key (encrypted at rest) and enable it.
2. Optionally map roles → providers and pick a model.
Nothing in the orchestration/business layer changes — the adapters already make
real API calls. The only reason connections show *unavailable* in this build is
that no real credentials are present.
