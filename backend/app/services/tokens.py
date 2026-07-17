"""JWT access/refresh token service.

Access tokens are short-lived and carry the user's identity and role. Refresh
tokens are long-lived and carry a ``ver`` claim matched against the employee's
``refresh_token_version`` so logout can invalidate all outstanding refresh
tokens by bumping that version.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired, or of the wrong type."""


@dataclass
class AccessClaims:
    subject: uuid.UUID
    role: str
    email: str


@dataclass
class RefreshClaims:
    subject: uuid.UUID
    version: int
    jti: str | None = None


class TokenService:
    def __init__(self):
        self._settings = get_settings()

    def _encode(self, payload: dict, expires: timedelta) -> str:
        now = datetime.now(timezone.utc)
        body = {**payload, "iat": now, "exp": now + expires}
        return jwt.encode(body, self._settings.jwt_secret, algorithm=self._settings.jwt_algorithm)

    def create_access_token(self, *, subject: uuid.UUID, role: str, email: str) -> str:
        return self._encode(
            {"sub": str(subject), "type": "access", "role": role, "email": email},
            timedelta(minutes=self._settings.access_token_minutes),
        )

    def create_refresh_token(
        self,
        *,
        subject: uuid.UUID,
        version: int,
        remember: bool = False,
        jti: str | None = None,
    ) -> str:
        days = (
            self._settings.refresh_token_remember_days
            if remember
            else self._settings.refresh_token_days
        )
        payload = {"sub": str(subject), "type": "refresh", "ver": version}
        if jti is not None:
            payload["jti"] = jti
        return self._encode(payload, timedelta(days=days))

    def _decode(self, token: str) -> dict:
        try:
            return jwt.decode(
                token, self._settings.jwt_secret, algorithms=[self._settings.jwt_algorithm]
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenError("Token has expired") from exc
        except jwt.PyJWTError as exc:
            raise TokenError("Invalid token") from exc

    def decode_access(self, token: str) -> AccessClaims:
        payload = self._decode(token)
        if payload.get("type") != "access":
            raise TokenError("Not an access token")
        try:
            return AccessClaims(
                subject=uuid.UUID(payload["sub"]),
                role=payload["role"],
                email=payload["email"],
            )
        except (KeyError, ValueError) as exc:
            raise TokenError("Malformed access token") from exc

    def decode_refresh(self, token: str) -> RefreshClaims:
        payload = self._decode(token)
        if payload.get("type") != "refresh":
            raise TokenError("Not a refresh token")
        try:
            return RefreshClaims(
                subject=uuid.UUID(payload["sub"]),
                version=int(payload["ver"]),
                jti=payload.get("jti"),
            )
        except (KeyError, ValueError) as exc:
            raise TokenError("Malformed refresh token") from exc
