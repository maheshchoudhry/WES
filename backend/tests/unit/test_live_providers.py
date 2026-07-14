"""Live provider adapter tests (Sprint 11).

Exercises the REAL request-building and response-parsing code paths of every
external provider using an injected ``httpx.MockTransport`` — no real API keys or
network. Also covers rate-limit detection, streaming, and the unconfigured guard.
"""

import httpx
import pytest

from app.providers.base import ExecutionRequest, Message, ProviderError, RateLimitError
from app.providers.registry import ProviderFactory


def _req():
    return ExecutionRequest(
        messages=[Message("system", "be brief"), Message("user", "hello")],
        max_tokens=16,
    )


def _provider(name, handler, extra=None):
    cfg = {"api_key": "test-key", "transport": httpx.MockTransport(handler)}
    if extra:
        cfg.update(extra)
    return ProviderFactory.create(name, cfg)


def test_claude_execute_builds_and_parses():
    seen = {}

    def handler(req):
        seen["url"] = str(req.url)
        seen["key"] = req.headers.get("x-api-key")
        seen["version"] = req.headers.get("anthropic-version")
        import json

        body = json.loads(req.content)
        seen["system"] = body.get("system")
        seen["messages"] = body["messages"]
        return httpx.Response(
            200,
            json={
                "model": "claude-opus-4-8",
                "content": [{"type": "text", "text": "brief answer"}],
                "usage": {"input_tokens": 11, "output_tokens": 3},
            },
        )

    p = _provider("claude", handler)
    result = p.execute(_req())
    assert result.output == "brief answer"
    assert result.prompt_tokens == 11 and result.completion_tokens == 3
    assert result.provider == "claude"
    assert seen["url"].endswith("/v1/messages")
    assert seen["key"] == "test-key"
    assert seen["system"] == "be brief"  # system message split out
    assert all(m["role"] in ("user", "assistant") for m in seen["messages"])


def test_openai_execute_builds_and_parses():
    def handler(req):
        assert req.headers.get("authorization") == "Bearer test-key"
        assert str(req.url).endswith("/v1/chat/completions")
        return httpx.Response(
            200,
            json={
                "model": "gpt-4o",
                "choices": [{"message": {"content": "hi there"}}],
                "usage": {"prompt_tokens": 8, "completion_tokens": 2},
            },
        )

    result = _provider("openai", handler).execute(_req())
    assert result.output == "hi there"
    assert result.total_tokens == 10


def test_openrouter_uses_openai_shape():
    def handler(req):
        assert "openrouter.ai" in str(req.url) or str(req.url).endswith("/v1/chat/completions")
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "routed"}}], "usage": {}}
        )

    result = _provider("openrouter", handler).execute(_req())
    assert result.output == "routed"


def test_gemini_execute_builds_and_parses():
    def handler(req):
        assert "generateContent" in str(req.url)
        assert "key=test-key" in str(req.url)
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "gemini says hi"}]}}],
                "usageMetadata": {"promptTokenCount": 7, "candidatesTokenCount": 4},
            },
        )

    result = _provider("gemini", handler).execute(_req())
    assert result.output == "gemini says hi"
    assert result.prompt_tokens == 7


def test_ollama_local_no_key():
    def handler(req):
        assert str(req.url).endswith("/api/chat")
        return httpx.Response(
            200,
            json={
                "model": "llama3",
                "message": {"content": "local answer"},
                "prompt_eval_count": 5,
                "eval_count": 6,
            },
        )

    # Ollama needs a base_url, not a key.
    p = ProviderFactory.create(
        "ollama", {"base_url": "http://localhost:11434", "transport": httpx.MockTransport(handler)}
    )
    result = p.execute(_req())
    assert result.output == "local answer"
    assert result.total_tokens == 11


def test_unconfigured_provider_refuses():
    p = ProviderFactory.create("claude", {})
    assert p.health().status == "unavailable"
    with pytest.raises(ProviderError):
        p.execute(_req())
    tc = p.test_connection()
    assert tc["ok"] is False and tc["status"] == "unavailable"


def test_rate_limit_detected():
    def handler(req):
        return httpx.Response(429, headers={"retry-after": "2"}, json={"error": "slow down"})

    with pytest.raises(RateLimitError) as exc:
        _provider("openai", handler).execute(_req())
    assert exc.value.retry_after == 2.0


def test_http_error_becomes_provider_error():
    def handler(req):
        return httpx.Response(500, text="boom")

    with pytest.raises(ProviderError):
        _provider("claude", handler).execute(_req())


def test_openai_streaming_yields_tokens():
    def handler(req):
        body = (
            'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
            "data: [DONE]\n\n"
        )
        return httpx.Response(200, text=body)

    tokens = list(_provider("openai", handler).stream(_req()))
    assert "".join(tokens) == "Hello"


def test_claude_test_connection_ok_with_mock():
    def handler(req):
        return httpx.Response(
            200,
            json={
                "model": "claude-opus-4-8",
                "content": [{"type": "text", "text": "pong"}],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    tc = _provider("claude", handler).test_connection()
    assert tc["ok"] is True and tc["status"] == "healthy"
    assert tc["model"] == "claude-opus-4-8"
