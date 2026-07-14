"""Encrypted secret store for provider credentials (Sprint 11).

Secrets (API keys) are NEVER stored in plaintext and NEVER returned to the UI.
They are encrypted at rest with an authenticated cipher keyed from
``WES_SECRET_KEY``:

- Preferred: Fernet (AES-128-CBC + HMAC-SHA256) from the ``cryptography`` package.
- Fallback: a stdlib authenticated cipher (HMAC-SHA256 keystream, encrypt-then-MAC)
  so the application still runs if ``cryptography`` is unavailable.

The public surface is identical regardless of backend: ``encrypt`` returns an
opaque token, ``decrypt`` recovers the plaintext (raising on tampering), and
``mask`` renders a safe display value that never reveals the secret.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

from app.core.config import get_settings

_MAGIC_STDLIB = "wes1:"  # marks the stdlib fallback format


def _derive_key(secret: str, length: int = 32) -> bytes:
    """Deterministically derive a fixed-length key from the configured secret."""
    return hashlib.sha256(secret.encode("utf-8")).digest()[:length]


class SecretBox:
    """Symmetric authenticated encryption for at-rest secrets."""

    def __init__(self, secret: str | None = None):
        self._secret = secret or get_settings().secret_key
        self._fernet = self._build_fernet(self._secret)

    @staticmethod
    def _build_fernet(secret: str):
        try:
            from cryptography.fernet import Fernet
        except Exception:  # pragma: no cover - exercised only without cryptography
            return None
        # Fernet needs a urlsafe-base64 32-byte key; derive it from the secret.
        key = base64.urlsafe_b64encode(_derive_key(secret, 32))
        return Fernet(key)

    # -- public API --------------------------------------------------------

    def encrypt(self, plaintext: str) -> str:
        if self._fernet is not None:
            return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")
        return self._encrypt_stdlib(plaintext)

    def decrypt(self, token: str) -> str:
        if token.startswith(_MAGIC_STDLIB):
            return self._decrypt_stdlib(token)
        if self._fernet is None:
            raise ValueError("Secret backend unavailable to decrypt this token")
        return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")

    # -- stdlib fallback (encrypt-then-MAC keystream cipher) ---------------

    def _encrypt_stdlib(self, plaintext: str) -> str:
        nonce = os.urandom(16)
        enc_key = _derive_key(self._secret + "enc")
        mac_key = _derive_key(self._secret + "mac")
        keystream = self._keystream(enc_key, nonce, len(plaintext.encode("utf-8")))
        data = bytes(a ^ b for a, b in zip(plaintext.encode("utf-8"), keystream))
        tag = hmac.new(mac_key, nonce + data, hashlib.sha256).digest()
        blob = base64.urlsafe_b64encode(nonce + tag + data).decode("ascii")
        return f"{_MAGIC_STDLIB}{blob}"

    def _decrypt_stdlib(self, token: str) -> str:
        raw = base64.urlsafe_b64decode(token[len(_MAGIC_STDLIB) :].encode("ascii"))
        nonce, tag, data = raw[:16], raw[16:48], raw[48:]
        mac_key = _derive_key(self._secret + "mac")
        expected = hmac.new(mac_key, nonce + data, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise ValueError("Secret token failed integrity check")
        enc_key = _derive_key(self._secret + "enc")
        keystream = self._keystream(enc_key, nonce, len(data))
        return bytes(a ^ b for a, b in zip(data, keystream)).decode("utf-8")

    @staticmethod
    def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < length:
            out.extend(hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest())
            counter += 1
        return bytes(out[:length])


def mask_secret(value: str | None) -> str | None:
    """Render a display-safe hint that never reveals the secret.

    None -> None; short -> "***"; longer -> last 4 chars, e.g. "••••••1234".
    """
    if not value:
        return None
    if len(value) <= 4:
        return "***"
    return "••••••" + value[-4:]


_box: SecretBox | None = None


def get_secret_box() -> SecretBox:
    """Return a process-wide SecretBox (keyed from settings)."""
    global _box
    if _box is None:
        _box = SecretBox()
    return _box
