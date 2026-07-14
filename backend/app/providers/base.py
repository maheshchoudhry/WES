"""The common provider interface every AI provider must implement.

No provider-specific types leak out of this module. Orchestration code depends on
``BaseProvider``, ``ExecutionRequest``, and ``ExecutionResult`` only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


class ProviderError(Exception):
    """Raised when a provider cannot fulfil a request (e.g. not configured)."""


class RateLimitError(ProviderError):
    """Raised when a provider signals rate limiting (HTTP 429).

    The orchestration layer treats this specially: back off and retry the same
    provider before failing over to another.
    """

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class Message:
    role: str  # system | user | assistant | tool
    content: str


@dataclass
class ExecutionRequest:
    messages: list[Message]
    model: str | None = None
    temperature: float = 0.2
    max_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_text(self) -> str:
        return "\n".join(f"{m.role}: {m.content}" for m in self.messages)

    def system_text(self) -> str:
        """Concatenated content of all system messages (for APIs with a system field)."""
        return "\n".join(m.content for m in self.messages if m.role == "system")

    def chat_messages(self, roles: tuple[str, ...] = ("user", "assistant", "tool")) -> list[dict]:
        """Non-system messages as ``{role, content}`` dicts (OpenAI-style APIs)."""
        return [{"role": m.role, "content": m.content} for m in self.messages if m.role in roles]


@dataclass
class ExecutionResult:
    output: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    currency: str
    latency_ms: int
    status: str = "completed"  # completed | failed
    error: str | None = None


@dataclass
class ProviderHealth:
    status: str  # healthy | degraded | unavailable
    detail: str | None = None


class BaseProvider(ABC):
    """Contract implemented by every provider."""

    name: str = "base"
    default_model: str = "default"
    # Cost per 1K tokens (input, output) in USD — override per provider.
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

    def __init__(self, config: dict[str, Any] | None = None):
        self.config: dict[str, Any] = config or {}
        self._initialized = False

    # -- lifecycle ---------------------------------------------------------

    @abstractmethod
    def initialize(self) -> None:
        """Prepare the provider (validate config, open clients)."""

    @abstractmethod
    def health(self) -> ProviderHealth:
        """Report provider availability without performing real work."""

    def test_connection(self) -> dict[str, Any]:
        """Actively test connectivity; return a structured status.

        Default derives from ``health()``; live providers override to make a real
        probe request. Never raises — always returns a renderable dict.
        """
        h = self.health()
        return {
            "ok": h.status == "healthy",
            "status": h.status,
            "detail": h.detail,
            "model": self.default_model,
            "version": "n/a",
        }

    # -- execution ---------------------------------------------------------

    @abstractmethod
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Run a single request and return a normalized result."""

    @abstractmethod
    def stream(self, request: ExecutionRequest) -> Iterator[str]:
        """Yield the response incrementally."""

    @abstractmethod
    def cancel(self, run_id: str) -> bool:
        """Attempt to cancel an in-flight run; returns True if acknowledged."""

    # -- estimation (provider-independent default heuristic) ---------------

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate (~4 chars/token). Providers may override."""
        return max(1, len(text) // 4)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return round(
            (prompt_tokens / 1000) * self.cost_per_1k_input
            + (completion_tokens / 1000) * self.cost_per_1k_output,
            6,
        )
