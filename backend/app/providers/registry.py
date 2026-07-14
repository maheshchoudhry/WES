"""Provider Registry and Factory.

The registry maps provider names to implementations; the factory instantiates a
provider from a name + config. This is the only place that knows the set of
concrete providers.
"""

from __future__ import annotations

from typing import Any

from app.providers.base import BaseProvider, ProviderError
from app.providers.external import (
    ClaudeProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
)
from app.providers.mock import MockProvider

_REGISTRY: dict[str, type[BaseProvider]] = {
    MockProvider.name: MockProvider,
    ClaudeProvider.name: ClaudeProvider,
    OpenAIProvider.name: OpenAIProvider,
    GeminiProvider.name: GeminiProvider,
    OpenRouterProvider.name: OpenRouterProvider,
    OllamaProvider.name: OllamaProvider,
}

PROVIDER_NAMES = list(_REGISTRY.keys())


class ProviderRegistry:
    @staticmethod
    def names() -> list[str]:
        return list(_REGISTRY.keys())

    @staticmethod
    def get(name: str) -> type[BaseProvider]:
        cls = _REGISTRY.get(name)
        if cls is None:
            raise ProviderError(f"Unknown provider '{name}'")
        return cls

    @staticmethod
    def register(name: str, cls: type[BaseProvider]) -> None:
        _REGISTRY[name] = cls


class ProviderFactory:
    @staticmethod
    def create(name: str, config: dict[str, Any] | None = None) -> BaseProvider:
        provider = ProviderRegistry.get(name)(config or {})
        provider.initialize()
        return provider
