"""External provider adapters (Claude, OpenAI, Gemini, OpenRouter, Ollama).

These implement the common interface but do NOT ship real API integrations or
keys. Without a configured key they report ``unavailable`` and refuse to execute.
Enabling a real provider in a future sprint means supplying a key/config in
Settings and implementing ``_call`` — no orchestration change required.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.providers.base import (
    BaseProvider,
    ExecutionRequest,
    ExecutionResult,
    ProviderError,
    ProviderHealth,
)


class ExternalProvider(BaseProvider):
    """Base for real providers; gated behind configuration (an API key)."""

    requires_key: bool = True
    key_field: str = "api_key"

    def initialize(self) -> None:
        self._initialized = True

    def _configured(self) -> bool:
        if not self.requires_key:
            return bool(self.config.get("base_url"))
        val = self.config.get(self.key_field)
        # Placeholder values (empty / "changeme" / "***") count as not configured.
        return bool(val) and val not in ("", "changeme", "***", "placeholder")

    def health(self) -> ProviderHealth:
        if self._configured():
            return ProviderHealth(status="healthy", detail=f"{self.name} configured.")
        return ProviderHealth(
            status="unavailable",
            detail=f"{self.name} is not configured (add an API key in Settings).",
        )

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if not self._configured():
            raise ProviderError(
                f"Provider '{self.name}' is not configured. Add an API key in Settings."
            )
        # A real integration would call the provider SDK here. Intentionally not
        # implemented in this sprint (no real keys / no network).
        raise ProviderError(f"Provider '{self.name}' has no live integration in this build.")

    def stream(self, request: ExecutionRequest) -> Iterator[str]:
        raise ProviderError(f"Provider '{self.name}' streaming is not available in this build.")

    def cancel(self, run_id: str) -> bool:
        return False


class ClaudeProvider(ExternalProvider):
    name = "claude"
    default_model = "claude-opus-4-8"
    cost_per_1k_input = 0.003
    cost_per_1k_output = 0.015


class OpenAIProvider(ExternalProvider):
    name = "openai"
    default_model = "gpt-4o"
    cost_per_1k_input = 0.0025
    cost_per_1k_output = 0.01


class GeminiProvider(ExternalProvider):
    name = "gemini"
    default_model = "gemini-1.5-pro"
    cost_per_1k_input = 0.00125
    cost_per_1k_output = 0.005


class OpenRouterProvider(ExternalProvider):
    name = "openrouter"
    default_model = "auto"
    cost_per_1k_input = 0.002
    cost_per_1k_output = 0.008


class OllamaProvider(ExternalProvider):
    name = "ollama"
    default_model = "llama3"
    requires_key = False  # local runtime; needs a base_url instead of a key
    cost_per_1k_input = 0.0
    cost_per_1k_output = 0.0
