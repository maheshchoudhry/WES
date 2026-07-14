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
