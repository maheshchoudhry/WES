"""Secret management service (Sprint 11).

Owns ``provider_secrets``: encrypts credentials at rest, scopes them to an
environment profile, supports rotation, validates format, and NEVER returns the
plaintext to callers (only a masked hint). Every change is audited to
``provider_events``. This is the only component that decrypts credentials, and it
hands them exclusively to the Provider Layer at execution time.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.secrets import get_secret_box, mask_secret
from app.models.provider_platform import ProviderEvent, ProviderSecret


def _now_env() -> str:
    return get_settings().active_environment


class SecretValidationError(ValueError):
    pass


class SecretService:
    def __init__(self, db: Session, actor: str = "System"):
        self.db = db
        self.actor = actor
        self.box = get_secret_box()

    # -- audit -------------------------------------------------------------

    def _audit(self, provider_id, event_type: str, detail: str) -> None:
        self.db.add(
            ProviderEvent(
                provider_id=provider_id,
                event_type=event_type,
                actor=self.actor,
                detail=detail,
                severity="info",
            )
        )

    # -- validation --------------------------------------------------------

    @staticmethod
    def validate(key_name: str, value: str) -> None:
        if value is None or len(value.strip()) < 8:
            raise SecretValidationError("Secret must be at least 8 characters")
        if value.strip() in {"changeme", "placeholder", "***"}:
            raise SecretValidationError("Secret must not be a placeholder value")

    # -- writes ------------------------------------------------------------

    def set_secret(
        self,
        provider_id: uuid.UUID,
        value: str,
        *,
        key_name: str = "api_key",
        environment: str | None = None,
    ) -> ProviderSecret:
        """Encrypt and store (or replace) a provider credential for an environment."""
        self.validate(key_name, value)
        environment = environment or _now_env()
        row = self.db.scalar(
            select(ProviderSecret).where(
                ProviderSecret.provider_id == provider_id,
                ProviderSecret.environment == environment,
                ProviderSecret.key_name == key_name,
            )
        )
        ciphertext = self.box.encrypt(value.strip())
        hint = mask_secret(value.strip())
        rotated = False
        if row is None:
            row = ProviderSecret(
                provider_id=provider_id,
                environment=environment,
                key_name=key_name,
                ciphertext=ciphertext,
                hint=hint,
            )
            self.db.add(row)
        else:
            row.ciphertext = ciphertext
            row.hint = hint
            from datetime import datetime, timezone

            row.last_rotated_at = datetime.now(timezone.utc)
            rotated = True
        self.db.flush()
        self._audit(
            provider_id,
            "secret.rotated" if rotated else "secret.set",
            f"{key_name} ({environment}) {'rotated' if rotated else 'set'}",
        )
        self.db.flush()
        return row

    def rotate(self, provider_id: uuid.UUID, value: str, **kw) -> ProviderSecret:
        return self.set_secret(provider_id, value, **kw)

    def delete_secret(
        self, provider_id: uuid.UUID, *, key_name: str = "api_key", environment: str | None = None
    ) -> None:
        environment = environment or _now_env()
        row = self.db.scalar(
            select(ProviderSecret).where(
                ProviderSecret.provider_id == provider_id,
                ProviderSecret.environment == environment,
                ProviderSecret.key_name == key_name,
            )
        )
        if row is not None:
            self.db.delete(row)
            self.db.flush()
            self._audit(provider_id, "secret.deleted", f"{key_name} ({environment}) removed")
            self.db.flush()

    # -- reads (never expose plaintext) ------------------------------------

    def get_plaintext(
        self, provider_id: uuid.UUID, *, key_name: str = "api_key", environment: str | None = None
    ) -> str | None:
        """Decrypt a secret for the Provider Layer only. Not exposed via the API."""
        environment = environment or _now_env()
        row = self.db.scalar(
            select(ProviderSecret).where(
                ProviderSecret.provider_id == provider_id,
                ProviderSecret.environment == environment,
                ProviderSecret.key_name == key_name,
            )
        )
        if row is None:
            return None
        try:
            return self.box.decrypt(row.ciphertext)
        except Exception:
            return None

    def secrets_for(self, provider_id: uuid.UUID, environment: str | None = None) -> dict[str, str]:
        """Decrypted credentials for a provider (Provider Layer use only)."""
        environment = environment or _now_env()
        rows = self.db.scalars(
            select(ProviderSecret).where(
                ProviderSecret.provider_id == provider_id,
                ProviderSecret.environment == environment,
            )
        ).all()
        out: dict[str, str] = {}
        for r in rows:
            try:
                out[r.key_name] = self.box.decrypt(r.ciphertext)
            except Exception:
                continue
        return out

    def list_masked(self, provider_id: uuid.UUID) -> list[dict]:
        """Masked hints for the UI (across environments). Never the plaintext."""
        rows = self.db.scalars(
            select(ProviderSecret).where(ProviderSecret.provider_id == provider_id)
        ).all()
        return [
            {
                "environment": r.environment,
                "key_name": r.key_name,
                "hint": r.hint or "***",
                "last_rotated_at": r.last_rotated_at.isoformat() if r.last_rotated_at else None,
                "configured": True,
            }
            for r in rows
        ]

    def has_secret(
        self, provider_id: uuid.UUID, *, key_name: str = "api_key", environment: str | None = None
    ) -> bool:
        environment = environment or _now_env()
        return (
            self.db.scalar(
                select(ProviderSecret).where(
                    ProviderSecret.provider_id == provider_id,
                    ProviderSecret.environment == environment,
                    ProviderSecret.key_name == key_name,
                )
            )
            is not None
        )
