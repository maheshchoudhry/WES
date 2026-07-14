"""Mock provider — a fully functional, deterministic provider for testing.

Requires no API keys. Produces a structured, role-aware response so the entire
orchestration pipeline can run end-to-end without any external service.
"""

from __future__ import annotations

import time
from collections.abc import Iterator

from app.providers.base import (
    BaseProvider,
    ExecutionRequest,
    ExecutionResult,
    ProviderHealth,
)


class MockProvider(BaseProvider):
    name = "mock"
    default_model = "mock-1"
    cost_per_1k_input = 0.0
    cost_per_1k_output = 0.0

    def initialize(self) -> None:
        self._initialized = True

    def health(self) -> ProviderHealth:
        return ProviderHealth(status="healthy", detail="Mock provider is always available.")

    def _respond(self, request: ExecutionRequest) -> str:
        role = request.metadata.get("role", "AI Employee")
        task = request.metadata.get("task", "the assigned task")
        return (
            f"[mock:{self.model_name(request)}] As the {role}, I have completed {task}. "
            "Output follows the SOP and meets the acceptance criteria. "
            "Ready for review and handoff to the next stage."
        )

    def model_name(self, request: ExecutionRequest) -> str:
        return request.model or self.default_model

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        start = time.perf_counter()
        prompt_tokens = self.estimate_tokens(request.as_text())
        output = self._respond(request)
        completion_tokens = self.estimate_tokens(output)
        latency_ms = int((time.perf_counter() - start) * 1000) + 5  # deterministic-ish
        total = prompt_tokens + completion_tokens
        return ExecutionResult(
            output=output,
            provider=self.name,
            model=self.model_name(request),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            cost=self.estimate_cost(prompt_tokens, completion_tokens),
            currency="USD",
            latency_ms=latency_ms,
            status="completed",
        )

    def stream(self, request: ExecutionRequest) -> Iterator[str]:
        for word in self._respond(request).split():
            yield word + " "

    def cancel(self, run_id: str) -> bool:
        return True
