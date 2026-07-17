"""Rate limiting middleware (WP5).

A lightweight in-memory fixed-window limiter, per client-IP and per route group
(auth vs. general). Off by default (``rate_limit_enabled``) so tests and existing
behavior are unaffected; enable it in a real deployment. A rejected request
returns 429 and records a security audit event.
"""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings

_WINDOW = 60.0
# (ip, group) -> list[timestamps] within the window.
_HITS: dict[tuple[str, str], list[float]] = defaultdict(list)


def reset_rate_limiter() -> None:
    """Clear all counters (used by tests)."""
    _HITS.clear()


def _group(path: str) -> str:
    return "auth" if path.startswith("/api/v1/auth") else "default"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        # Only guard state-changing / auth traffic; reads stay unthrottled here.
        group = _group(path)
        limit = settings.rate_limit_auth if group == "auth" else settings.rate_limit_default
        ip = request.client.host if request.client else "unknown"
        key = (ip, group)
        now = time.monotonic()
        window = [t for t in _HITS[key] if now - t < _WINDOW]
        window.append(now)
        _HITS[key] = window

        if len(window) > limit:
            self._record_block(ip, path)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please slow down.",
                    }
                },
            )
        return await call_next(request)

    @staticmethod
    def _record_block(ip: str, path: str) -> None:
        try:
            from app.core.database import SessionLocal
            from app.services.audit import AuditService

            db = SessionLocal()
            try:
                AuditService(db).security_event(
                    "rate_limit_exceeded",
                    ip=ip,
                    detail=f"Rate limit exceeded for {path}",
                    severity="warning",
                )
                db.commit()
            finally:
                db.close()
        except Exception:  # pragma: no cover - never break the response path
            pass
