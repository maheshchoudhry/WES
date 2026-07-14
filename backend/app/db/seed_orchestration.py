"""Seed data for the AI Orchestration Engine (Sprint 09).

Registers the six providers (Mock enabled + default; Claude/OpenAI/Gemini/
OpenRouter/Ollama disabled with placeholder configs, NO real keys), maps every AI
role to the Mock provider, records provider health, and runs one sample pipeline
execution through the Mock provider. Idempotent (skips when providers exist).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ai import AIEmployee, AIRole
from app.models.orchestration import AIProvider, ProviderConfig
from app.models.provider_platform import BudgetConfig, ProviderModel
from app.models.work import WorkItem

# name, display_name, enabled, is_default, default_model, priority
PROVIDERS = [
    ("mock", "Mock Provider", True, True, "mock-1", 10),
    ("claude", "Anthropic Claude", False, False, "claude-opus-4-8", 20),
    ("openai", "OpenAI", False, False, "gpt-4o", 30),
    ("gemini", "Google Gemini", False, False, "gemini-1.5-pro", 40),
    ("openrouter", "OpenRouter", False, False, "openrouter/auto", 50),
    ("ollama", "Ollama (local)", False, False, "llama3", 60),
]

# provider -> [(code, display_name, is_default, context_window, in_cost/1k, out_cost/1k)]
MODELS = {
    "mock": [("mock-1", "Mock 1", True, 8000, 0.0, 0.0)],
    "claude": [
        ("claude-opus-4-8", "Claude Opus 4.8", True, 200000, 0.003, 0.015),
        ("claude-sonnet-5", "Claude Sonnet 5", False, 200000, 0.001, 0.005),
    ],
    "openai": [
        ("gpt-4o", "GPT-4o", True, 128000, 0.0025, 0.01),
        ("gpt-4.1", "GPT-4.1", False, 128000, 0.002, 0.008),
    ],
    "gemini": [("gemini-1.5-pro", "Gemini 1.5 Pro", True, 1000000, 0.00125, 0.005)],
    "openrouter": [("openrouter/auto", "Auto (OpenRouter)", True, 128000, 0.002, 0.008)],
    "ollama": [("llama3", "Llama 3 (local)", True, 8000, 0.0, 0.0)],
}


def seed_orchestration(db: Session) -> bool:
    """Seed providers, role mappings, health, and a sample run. Idempotent."""
    if db.query(AIProvider).count() > 0:
        return False

    providers: dict[str, AIProvider] = {}
    for name, display, enabled, is_default, model, priority in PROVIDERS:
        p = AIProvider(
            name=name,
            display_name=display,
            enabled=enabled,
            is_default=is_default,
            default_model=model,
            active_model=model,
            priority=priority,
        )
        db.add(p)
        providers[name] = p
    db.flush()

    # Selectable models per provider (with per-model pricing).
    for name, models in MODELS.items():
        for code, disp, is_default, ctx, cin, cout in models:
            db.add(
                ProviderModel(
                    provider_id=providers[name].id,
                    code=code,
                    display_name=disp,
                    is_default=is_default,
                    context_window=ctx,
                    input_cost_per_1k=cin,
                    output_cost_per_1k=cout,
                )
            )

    # Global budget guardrails (generous defaults; founder tunes in Settings).
    db.add(
        BudgetConfig(
            scope="global",
            daily_cost_limit=50.0,
            monthly_cost_limit=1000.0,
            max_cost=5.0,
            max_tokens=200000,
            warning_threshold=0.8,
            hard_stop=True,
        )
    )
    db.flush()

    # Placeholder configs for external providers (no real secrets).
    for name in ("claude", "openai", "gemini", "openrouter"):
        db.add(ProviderConfig(provider_id=providers[name].id, key="api_key", value="changeme"))
        db.add(
            ProviderConfig(
                provider_id=providers[name].id, key="model", value=providers[name].default_model
            )
        )
    db.add(ProviderConfig(provider_id=providers["ollama"].id, key="base_url", value=""))

    # Map every AI role -> Mock provider (role:<code> config rows on Mock).
    mock = providers["mock"]
    for role in db.query(AIRole).all():
        db.add(ProviderConfig(provider_id=mock.id, key=f"role:{role.code}", value=role.code))
    db.flush()

    # Record provider health (Mock healthy; externals unavailable without keys).
    from app.services.providers_service import ProviderService

    ProviderService(db).check_health()

    # Run one sample pipeline execution through the Mock provider.
    from app.services.orchestration import OrchestrationService

    backend = db.query(AIEmployee).filter(AIEmployee.employee_code == "AI-EMP-005").one_or_none()
    task = db.query(WorkItem).filter(WorkItem.task_code == "WORLD-004").one_or_none()
    if backend is not None:
        OrchestrationService(db, actor="Founder").run_stage(
            backend.id, task.id if task else None, provider_name="mock"
        )

    return True
