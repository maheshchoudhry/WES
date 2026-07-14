"""Live external provider adapters (Sprint 11).

Each adapter implements the common ``BaseProvider`` interface against the real
HTTP API of its provider — Anthropic Claude, OpenAI, Google Gemini, OpenRouter,
and Ollama. When a credential is configured the adapter makes a real API call;
without one it reports ``unavailable`` and refuses to execute (so business logic
never depends on a provider being reachable).

Provider-specific request building and response parsing live ONLY here, behind
the interface. Orchestration never imports these classes — it goes through the
registry/factory. Enabling a provider in production is purely a Settings action:
enter an API key, and execution flows through it with no architecture change.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

from app.providers.base import (
    BaseProvider,
    ExecutionRequest,
    ExecutionResult,
    Message,
    ProviderError,
    ProviderHealth,
)
from app.providers.http import parse_json, post_json, stream_sse

_PLACEHOLDERS = {"", "changeme", "***", "placeholder"}


class ExternalProvider(BaseProvider):
    """Base for real providers; gated behind configuration (an API key/base URL)."""

    requires_key: bool = True
    key_field: str = "api_key"
    default_base_url: str = ""
    api_version: str = "v1"

    def initialize(self) -> None:
        self._initialized = True

    # -- configuration -----------------------------------------------------

    def _api_key(self) -> str | None:
        val = self.config.get(self.key_field)
        if not val or val in _PLACEHOLDERS:
            return None
        return val

    def _base_url(self) -> str:
        return (self.config.get("base_url") or self.default_base_url).rstrip("/")

    def _model(self, request: ExecutionRequest) -> str:
        return request.model or self.config.get("model") or self.default_model

    def _timeout(self) -> float:
        try:
            return float(self.config.get("timeout") or 60.0)
        except (TypeError, ValueError):
            return 60.0

    def _transport(self):
        # Tests inject an httpx.MockTransport here; production leaves it None.
        return self.config.get("transport")

    def _configured(self) -> bool:
        if not self.requires_key:
            return bool(self._base_url())
        return self._api_key() is not None

    # -- health ------------------------------------------------------------

    def health(self) -> ProviderHealth:
        if self._configured():
            return ProviderHealth(status="healthy", detail=f"{self.name} configured.")
        missing = "base URL" if not self.requires_key else "API key"
        return ProviderHealth(
            status="unavailable",
            detail=f"{self.name} is not configured (set a {missing} in Settings).",
        )

    def test_connection(self) -> dict[str, Any]:
        """Attempt a minimal real request; report status/model/version/limits.

        Never raises — returns a structured result the UI/health monitor renders.
        """
        if not self._configured():
            return {
                "ok": False,
                "status": "unavailable",
                "detail": self.health().detail,
                "model": self.default_model,
                "version": self.api_version,
            }
        probe = ExecutionRequest(
            messages=[Message(role="user", content="ping")],
            max_tokens=1,
        )
        started = time.monotonic()
        try:
            result = self.execute(probe)
            latency = int((time.monotonic() - started) * 1000)
            return {
                "ok": True,
                "status": "healthy",
                "detail": f"{self.name} reachable.",
                "model": result.model,
                "version": self.api_version,
                "latency_ms": latency,
            }
        except ProviderError as exc:
            return {
                "ok": False,
                "status": "unavailable",
                "detail": str(exc),
                "model": self._model(probe),
                "version": self.api_version,
            }

    # -- execution ---------------------------------------------------------

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if not self._configured():
            raise ProviderError(
                f"Provider '{self.name}' is not configured. Add an API key in Settings."
            )
        started = time.monotonic()
        text, prompt_tokens, completion_tokens, model = self._call(request)
        latency_ms = int((time.monotonic() - started) * 1000)
        if not prompt_tokens:
            prompt_tokens = self.estimate_tokens(request.as_text())
        if not completion_tokens:
            completion_tokens = self.estimate_tokens(text)
        total = prompt_tokens + completion_tokens
        return ExecutionResult(
            output=text,
            provider=self.name,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            cost=self.estimate_cost(prompt_tokens, completion_tokens),
            currency="USD",
            latency_ms=latency_ms,
            status="completed",
        )

    def stream(self, request: ExecutionRequest) -> Iterator[str]:
        if not self._configured():
            raise ProviderError(
                f"Provider '{self.name}' is not configured. Add an API key in Settings."
            )
        yield from self._stream(request)

    def cancel(self, run_id: str) -> bool:
        # HTTP requests are cancelled by closing the stream client-side; the
        # execution layer owns the cancellation registry.
        return True

    # -- per-provider hooks (implemented by subclasses) --------------------

    def _call(self, request: ExecutionRequest) -> tuple[str, int, int, str]:
        """Return (text, prompt_tokens, completion_tokens, model)."""
        raise NotImplementedError

    def _stream(self, request: ExecutionRequest) -> Iterator[str]:
        raise NotImplementedError


class ClaudeProvider(ExternalProvider):
    name = "claude"
    default_model = "claude-opus-4-8"
    default_base_url = "https://api.anthropic.com"
    api_version = "2023-06-01"
    cost_per_1k_input = 0.003
    cost_per_1k_output = 0.015

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._api_key(),
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }

    def _body(self, request: ExecutionRequest, stream: bool) -> dict:
        model = self._model(request)
        body: dict[str, Any] = {
            "model": model,
            "max_tokens": request.max_tokens or 1024,
            "messages": request.chat_messages(("user", "assistant")),
        }
        system = request.system_text()
        if system:
            body["system"] = system
        if stream:
            body["stream"] = True
        return body

    def _call(self, request: ExecutionRequest) -> tuple[str, int, int, str]:
        data = post_json(
            provider=self.name,
            base_url=self._base_url(),
            path="/v1/messages",
            headers=self._headers(),
            json_body=self._body(request, stream=False),
            timeout=self._timeout(),
            transport=self._transport(),
        )
        blocks = data.get("content") or []
        text = "".join(b.get("text", "") for b in blocks if b.get("type", "text") == "text")
        usage = data.get("usage") or {}
        return (
            text,
            int(usage.get("input_tokens") or 0),
            int(usage.get("output_tokens") or 0),
            data.get("model") or self._model(request),
        )

    def _stream(self, request: ExecutionRequest) -> Iterator[str]:
        for payload in stream_sse(
            provider=self.name,
            base_url=self._base_url(),
            path="/v1/messages",
            headers=self._headers(),
            json_body=self._body(request, stream=True),
            timeout=self._timeout(),
            transport=self._transport(),
        ):
            evt = parse_json(payload)
            if evt and evt.get("type") == "content_block_delta":
                delta = evt.get("delta") or {}
                if delta.get("text"):
                    yield delta["text"]


class _OpenAICompatible(ExternalProvider):
    """OpenAI-style /chat/completions provider (OpenAI + OpenRouter)."""

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key()}",
            "content-type": "application/json",
        }

    def _body(self, request: ExecutionRequest, stream: bool) -> dict:
        body: dict[str, Any] = {
            "model": self._model(request),
            "messages": [
                {"role": m.role, "content": m.content}
                for m in request.messages
                if m.role in ("system", "user", "assistant")
            ],
            "temperature": request.temperature,
        }
        if request.max_tokens:
            body["max_tokens"] = request.max_tokens
        if stream:
            body["stream"] = True
        return body

    def _call(self, request: ExecutionRequest) -> tuple[str, int, int, str]:
        data = post_json(
            provider=self.name,
            base_url=self._base_url(),
            path="/v1/chat/completions",
            headers=self._headers(),
            json_body=self._body(request, stream=False),
            timeout=self._timeout(),
            transport=self._transport(),
        )
        choice = (data.get("choices") or [{}])[0]
        text = (choice.get("message") or {}).get("content") or ""
        usage = data.get("usage") or {}
        return (
            text,
            int(usage.get("prompt_tokens") or 0),
            int(usage.get("completion_tokens") or 0),
            data.get("model") or self._model(request),
        )

    def _stream(self, request: ExecutionRequest) -> Iterator[str]:
        for payload in stream_sse(
            provider=self.name,
            base_url=self._base_url(),
            path="/v1/chat/completions",
            headers=self._headers(),
            json_body=self._body(request, stream=True),
            timeout=self._timeout(),
            transport=self._transport(),
        ):
            evt = parse_json(payload)
            if not evt:
                continue
            delta = ((evt.get("choices") or [{}])[0].get("delta") or {}).get("content")
            if delta:
                yield delta


class OpenAIProvider(_OpenAICompatible):
    name = "openai"
    default_model = "gpt-4o"
    default_base_url = "https://api.openai.com"
    api_version = "v1"
    cost_per_1k_input = 0.0025
    cost_per_1k_output = 0.01


class OpenRouterProvider(_OpenAICompatible):
    name = "openrouter"
    default_model = "openrouter/auto"
    default_base_url = "https://openrouter.ai/api"
    api_version = "v1"
    cost_per_1k_input = 0.002
    cost_per_1k_output = 0.008


class GeminiProvider(ExternalProvider):
    name = "gemini"
    default_model = "gemini-1.5-pro"
    default_base_url = "https://generativelanguage.googleapis.com"
    api_version = "v1beta"
    cost_per_1k_input = 0.00125
    cost_per_1k_output = 0.005

    def _headers(self) -> dict[str, str]:
        return {"content-type": "application/json"}

    def _body(self, request: ExecutionRequest) -> dict:
        contents = [
            {
                "role": "user" if m.role in ("user", "system") else "model",
                "parts": [{"text": m.content}],
            }
            for m in request.messages
            if m.role in ("user", "assistant", "system")
        ]
        body: dict[str, Any] = {"contents": contents}
        if request.max_tokens:
            body["generationConfig"] = {"maxOutputTokens": request.max_tokens}
        return body

    def _call(self, request: ExecutionRequest) -> tuple[str, int, int, str]:
        model = self._model(request)
        data = post_json(
            provider=self.name,
            base_url=self._base_url(),
            path=f"/{self.api_version}/models/{model}:generateContent",
            headers=self._headers(),
            json_body=self._body(request),
            timeout=self._timeout(),
            params={"key": self._api_key()},
            transport=self._transport(),
        )
        cand = (data.get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata") or {}
        return (
            text,
            int(usage.get("promptTokenCount") or 0),
            int(usage.get("candidatesTokenCount") or 0),
            model,
        )

    def _stream(self, request: ExecutionRequest) -> Iterator[str]:
        model = self._model(request)
        for payload in stream_sse(
            provider=self.name,
            base_url=self._base_url(),
            path=f"/{self.api_version}/models/{model}:streamGenerateContent",
            headers=self._headers(),
            json_body=self._body(request),
            timeout=self._timeout(),
            params={"key": self._api_key(), "alt": "sse"},
            transport=self._transport(),
        ):
            evt = parse_json(payload)
            if not evt:
                continue
            cand = (evt.get("candidates") or [{}])[0]
            parts = (cand.get("content") or {}).get("parts") or []
            for p in parts:
                if p.get("text"):
                    yield p["text"]


class OllamaProvider(ExternalProvider):
    name = "ollama"
    default_model = "llama3"
    default_base_url = "http://localhost:11434"
    api_version = "api"
    requires_key = False  # local runtime; needs a base_url instead of a key
    cost_per_1k_input = 0.0
    cost_per_1k_output = 0.0

    def _body(self, request: ExecutionRequest, stream: bool) -> dict:
        return {
            "model": self._model(request),
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": stream,
        }

    def _call(self, request: ExecutionRequest) -> tuple[str, int, int, str]:
        data = post_json(
            provider=self.name,
            base_url=self._base_url(),
            path="/api/chat",
            headers={"content-type": "application/json"},
            json_body=self._body(request, stream=False),
            timeout=self._timeout(),
            transport=self._transport(),
        )
        text = (data.get("message") or {}).get("content") or ""
        return (
            text,
            int(data.get("prompt_eval_count") or 0),
            int(data.get("eval_count") or 0),
            data.get("model") or self._model(request),
        )

    def _stream(self, request: ExecutionRequest) -> Iterator[str]:
        for payload in stream_sse(
            provider=self.name,
            base_url=self._base_url(),
            path="/api/chat",
            headers={"content-type": "application/json"},
            json_body=self._body(request, stream=True),
            timeout=self._timeout(),
            transport=self._transport(),
        ):
            evt = parse_json(payload)
            if evt and (evt.get("message") or {}).get("content"):
                yield evt["message"]["content"]
