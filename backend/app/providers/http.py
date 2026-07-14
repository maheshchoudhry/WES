"""Shared HTTP transport for live provider integrations (Sprint 11).

All external providers speak HTTP. This module centralizes the httpx client
construction, timeouts, error normalization (network/HTTP errors ->
``ProviderError``; HTTP 429 -> ``RateLimitError``), and Server-Sent-Events
parsing for streaming. It contains NO provider-specific logic — each provider
supplies its own URL, headers, and body.

Tests inject a deterministic ``httpx.MockTransport`` via ``config["transport"]``,
so the real request-building and response-parsing code paths are exercised
without real API keys or network access.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx

from app.providers.base import ProviderError, RateLimitError


def build_client(
    *,
    base_url: str,
    timeout: float,
    transport: Any | None = None,
) -> httpx.Client:
    """Construct an httpx client. ``transport`` (tests) overrides the network."""
    kwargs: dict[str, Any] = {"base_url": base_url, "timeout": timeout}
    if transport is not None:
        kwargs["transport"] = transport
    return httpx.Client(**kwargs)


def _raise_for_status(resp: httpx.Response, provider: str) -> None:
    if resp.status_code == 429:
        retry_after = resp.headers.get("retry-after")
        raise RateLimitError(
            f"{provider} rate limited (HTTP 429)",
            retry_after=float(retry_after) if retry_after and retry_after.isdigit() else None,
        )
    if resp.status_code >= 400:
        body = resp.text[:300]
        raise ProviderError(f"{provider} API error HTTP {resp.status_code}: {body}")


def post_json(
    *,
    provider: str,
    base_url: str,
    path: str,
    headers: dict[str, str],
    json_body: dict[str, Any],
    timeout: float,
    params: dict[str, Any] | None = None,
    transport: Any | None = None,
) -> dict[str, Any]:
    """POST JSON and return the parsed response, normalizing errors."""
    try:
        with build_client(base_url=base_url, timeout=timeout, transport=transport) as client:
            resp = client.post(path, headers=headers, json=json_body, params=params)
            _raise_for_status(resp, provider)
            return resp.json()
    except (RateLimitError, ProviderError):
        raise
    except httpx.HTTPError as exc:
        raise ProviderError(f"{provider} connection failed: {exc}") from exc


def stream_sse(
    *,
    provider: str,
    base_url: str,
    path: str,
    headers: dict[str, str],
    json_body: dict[str, Any],
    timeout: float,
    params: dict[str, Any] | None = None,
    transport: Any | None = None,
) -> Iterator[str]:
    """Stream a Server-Sent-Events response, yielding raw ``data:`` payloads."""
    try:
        with build_client(base_url=base_url, timeout=timeout, transport=transport) as client:
            with client.stream(
                "POST", path, headers=headers, json=json_body, params=params
            ) as resp:
                if resp.status_code >= 400:
                    resp.read()
                    _raise_for_status(resp, provider)
                for line in resp.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        payload = line[len("data:") :].strip()
                        if payload and payload != "[DONE]":
                            yield payload
                    elif line.startswith("{"):
                        # Some APIs (Ollama) stream bare JSON lines, not SSE.
                        yield line
    except (RateLimitError, ProviderError):
        raise
    except httpx.HTTPError as exc:
        raise ProviderError(f"{provider} streaming failed: {exc}") from exc


def parse_json(payload: str) -> dict[str, Any] | None:
    try:
        return json.loads(payload)
    except (ValueError, TypeError):
        return None
