"""Provider Abstraction Layer.

Business logic must never know which concrete provider (Claude, OpenAI, Gemini,
OpenRouter, Ollama, or the Mock) is executing — it talks only to ``BaseProvider``
via the ``ProviderFactory``.
"""

from app.providers.base import (
    BaseProvider,
    ExecutionRequest,
    ExecutionResult,
    Message,
    ProviderError,
    ProviderHealth,
)
from app.providers.registry import PROVIDER_NAMES, ProviderFactory, ProviderRegistry

__all__ = [
    "BaseProvider",
    "ExecutionRequest",
    "ExecutionResult",
    "Message",
    "ProviderHealth",
    "ProviderError",
    "ProviderRegistry",
    "ProviderFactory",
    "PROVIDER_NAMES",
]
