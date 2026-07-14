"""Unit tests for the Provider Abstraction Layer."""

import pytest

from app.providers import (
    PROVIDER_NAMES,
    ExecutionRequest,
    Message,
    ProviderError,
    ProviderFactory,
    ProviderRegistry,
)


def _request() -> ExecutionRequest:
    return ExecutionRequest(
        messages=[
            Message(role="system", content="You are an AI employee."),
            Message(role="user", content="Do the task."),
        ],
        metadata={"role": "Backend Engineer", "task": "build API"},
    )


def test_registry_lists_all_providers():
    assert set(PROVIDER_NAMES) == {"mock", "claude", "openai", "gemini", "openrouter", "ollama"}


def test_unknown_provider_raises():
    with pytest.raises(ProviderError):
        ProviderRegistry.get("nope")


def test_mock_provider_executes():
    provider = ProviderFactory.create("mock")
    assert provider.health().status == "healthy"
    result = provider.execute(_request())
    assert result.status == "completed"
    assert result.provider == "mock"
    assert result.total_tokens == result.prompt_tokens + result.completion_tokens
    assert "Backend Engineer" in result.output


def test_mock_provider_streams():
    provider = ProviderFactory.create("mock")
    chunks = list(provider.stream(_request()))
    assert len(chunks) > 0


def test_external_provider_unavailable_without_key():
    provider = ProviderFactory.create("claude", {})
    assert provider.health().status == "unavailable"
    with pytest.raises(ProviderError):
        provider.execute(_request())


def test_external_provider_configured_by_key():
    provider = ProviderFactory.create("openai", {"api_key": "sk-real-key"})
    # Configured -> healthy, though it has no live integration in this build.
    assert provider.health().status == "healthy"


def test_estimate_tokens_and_cost():
    provider = ProviderFactory.create("claude", {"api_key": "x"})
    tokens = provider.estimate_tokens("word " * 100)
    assert tokens > 0
    cost = provider.estimate_cost(1000, 1000)
    assert cost == pytest.approx(0.003 + 0.015)


def test_business_logic_is_provider_independent():
    # Same request, two providers, one interface — the caller never branches on type.
    for name in ("mock", "claude"):
        provider = ProviderFactory.create(name, {"api_key": "x"} if name != "mock" else {})
        assert hasattr(provider, "execute")
        assert hasattr(provider, "health")
        assert hasattr(provider, "estimate_cost")
