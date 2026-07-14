"""Provider service — registry-backed provider settings, role mapping, health.

Owns the ai_providers / provider_configs rows and resolves a concrete provider
instance (via the ProviderFactory) for a given AI employee. All provider-specific
behavior lives behind the Provider Abstraction Layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.ai import AIEmployee, AIRole
from app.models.orchestration import AIProvider, ProviderConfig, ProviderHealthRecord
from app.providers import PROVIDER_NAMES, ProviderFactory, ProviderRegistry

_ROLE_PREFIX = "role:"


class ProviderService:
    def __init__(self, db: Session):
        self.db = db

    # -- reads -------------------------------------------------------------

    def list_providers(self) -> list[AIProvider]:
        return list(self.db.scalars(select(AIProvider).order_by(AIProvider.name)).all())

    def get(self, provider_id: uuid.UUID) -> AIProvider:
        p = self.db.get(AIProvider, provider_id)
        if p is None:
            raise NotFoundError(f"Provider {provider_id} not found")
        return p

    def get_by_name(self, name: str) -> AIProvider | None:
        return self.db.scalar(select(AIProvider).where(AIProvider.name == name))

    def default_provider(self) -> AIProvider | None:
        return self.db.scalar(select(AIProvider).where(AIProvider.is_default.is_(True)))

    def config_dict(self, provider: AIProvider) -> dict:
        rows = self.db.scalars(
            select(ProviderConfig).where(ProviderConfig.provider_id == provider.id)
        ).all()
        return {c.key: c.value for c in rows if not c.key.startswith(_ROLE_PREFIX)}

    def serialize(self, p: AIProvider) -> dict:
        health = self.db.scalar(
            select(ProviderHealthRecord)
            .where(ProviderHealthRecord.provider_id == p.id)
            .order_by(ProviderHealthRecord.checked_at.desc())
        )
        cfg = self.config_dict(p)
        # Mask any secret-like values.
        masked = {k: ("***" if "key" in k.lower() and v else v) for k, v in cfg.items()}
        return {
            "id": str(p.id),
            "name": p.name,
            "display_name": p.display_name,
            "enabled": p.enabled,
            "is_default": p.is_default,
            "default_model": p.default_model,
            "config": masked,
            "health": (
                (health.status.value if hasattr(health.status, "value") else health.status)
                if health
                else "unknown"
            ),
        }

    # -- settings ----------------------------------------------------------

    def set_enabled(self, provider_id: uuid.UUID, enabled: bool) -> AIProvider:
        p = self.get(provider_id)
        p.enabled = enabled
        self.db.flush()
        return p

    def set_default(self, provider_id: uuid.UUID) -> AIProvider:
        p = self.get(provider_id)
        if not p.enabled:
            raise ValidationError("Enable the provider before making it the default")
        for other in self.list_providers():
            other.is_default = other.id == p.id
        self.db.flush()
        return p

    def set_config(self, provider_id: uuid.UUID, key: str, value: str | None) -> None:
        p = self.get(provider_id)
        row = self.db.scalar(
            select(ProviderConfig).where(
                ProviderConfig.provider_id == p.id, ProviderConfig.key == key
            )
        )
        if row is None:
            self.db.add(ProviderConfig(provider_id=p.id, key=key, value=value))
        else:
            row.value = value
        self.db.flush()

    # -- role -> provider mapping (stored as provider_configs) -------------

    def map_role(self, role_code: str, provider_name: str) -> None:
        provider = self.get_by_name(provider_name)
        if provider is None:
            raise ValidationError(f"Unknown provider '{provider_name}'")
        key = f"{_ROLE_PREFIX}{role_code}"
        # Remove any existing mapping for this role on any provider.
        for row in self.db.scalars(select(ProviderConfig).where(ProviderConfig.key == key)).all():
            self.db.delete(row)
        self.db.flush()
        self.db.add(ProviderConfig(provider_id=provider.id, key=key, value=role_code))
        self.db.flush()

    def role_mappings(self) -> dict:
        rows = self.db.scalars(
            select(ProviderConfig).where(ProviderConfig.key.like(f"{_ROLE_PREFIX}%"))
        ).all()
        names = {p.id: p.name for p in self.list_providers()}
        return {r.key[len(_ROLE_PREFIX) :]: names.get(r.provider_id) for r in rows}

    def provider_for_employee(self, employee: AIEmployee) -> AIProvider:
        role: AIRole | None = self.db.get(AIRole, employee.role_id) if employee.role_id else None
        if role is not None:
            mapping = self.db.scalar(
                select(ProviderConfig).where(ProviderConfig.key == f"{_ROLE_PREFIX}{role.code}")
            )
            if mapping is not None:
                p = self.db.get(AIProvider, mapping.provider_id)
                if p is not None and p.enabled:
                    return p
        default = self.default_provider()
        if default is None:
            raise ValidationError("No default provider configured")
        return default

    # -- factory + health --------------------------------------------------

    def instance_for(self, provider: AIProvider):
        return ProviderFactory.create(provider.name, self.config_dict(provider))

    def check_health(self) -> list[dict]:
        results = []
        for p in self.list_providers():
            try:
                inst = self.instance_for(p)
                h = inst.health()
                status, detail = h.status, h.detail
            except Exception as exc:  # pragma: no cover - defensive
                status, detail = "unavailable", str(exc)
            self.db.add(ProviderHealthRecord(provider_id=p.id, status=status, detail=detail))
            results.append({"name": p.name, "status": status, "detail": detail})
        self.db.flush()
        return results

    @staticmethod
    def known_provider_names() -> list[str]:
        return list(PROVIDER_NAMES)

    @staticmethod
    def registry_has(name: str) -> bool:
        return name in ProviderRegistry.names()


def _now() -> datetime:
    return datetime.now(timezone.utc)
