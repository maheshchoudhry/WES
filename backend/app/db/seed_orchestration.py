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
from app.models.work import WorkItem

# name, display_name, enabled, is_default, default_model
PROVIDERS = [
    ("mock", "Mock Provider", True, True, "mock-1"),
    ("claude", "Anthropic Claude", False, False, "claude-opus-4-8"),
    ("openai", "OpenAI", False, False, "gpt-4o"),
    ("gemini", "Google Gemini", False, False, "gemini-1.5-pro"),
    ("openrouter", "OpenRouter", False, False, "auto"),
    ("ollama", "Ollama (local)", False, False, "llama3"),
]


def seed_orchestration(db: Session) -> bool:
    """Seed providers, role mappings, health, and a sample run. Idempotent."""
    if db.query(AIProvider).count() > 0:
        return False

    providers: dict[str, AIProvider] = {}
    for name, display, enabled, is_default, model in PROVIDERS:
        p = AIProvider(
            name=name,
            display_name=display,
            enabled=enabled,
            is_default=is_default,
            default_model=model,
        )
        db.add(p)
        providers[name] = p
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
