"""Provider Platform services (Sprint 11).

Cost engine, metrics, failover routing, health monitoring, and the founder/AI
platform dashboards. These sit above the ProviderService and the Provider Layer;
they never talk to external APIs directly (only the Provider Layer does).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai import AIEmployee
from app.models.orchestration import AIProvider, ExecutionRun
from app.models.provider_platform import (
    ProviderBilling,
    ProviderErrorLog,
    ProviderEvent,
    ProviderLatency,
    ProviderUsage,
)
from app.providers.base import ExecutionResult
from app.services.budget_service import BudgetService
from app.services.providers_service import ProviderService


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CostEngine:
    """Records per-execution usage and rolls it up into billing periods."""

    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        provider: AIProvider,
        result: ExecutionResult,
        *,
        run_id: uuid.UUID | None = None,
        ai_employee_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
    ) -> ProviderUsage:
        now = _now()
        day, month = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")
        usage = ProviderUsage(
            provider_id=provider.id,
            run_id=run_id,
            ai_employee_id=ai_employee_id,
            project_id=project_id,
            model=result.model,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            estimated_cost=result.cost,
            actual_cost=result.cost,
            currency=result.currency,
            day=day,
            month=month,
        )
        self.db.add(usage)
        self._roll(provider.id, "day", day, result)
        self._roll(provider.id, "month", month, result)
        self.db.flush()
        return usage

    def _roll(self, provider_id, period: str, key: str, result: ExecutionResult) -> None:
        row = self.db.scalar(
            select(ProviderBilling).where(
                ProviderBilling.provider_id == provider_id,
                ProviderBilling.period == period,
                ProviderBilling.period_key == key,
            )
        )
        if row is None:
            row = ProviderBilling(
                provider_id=provider_id,
                period=period,
                period_key=key,
                tokens=result.total_tokens,
                cost=result.cost,
                currency=result.currency,
            )
            self.db.add(row)
        else:
            row.tokens += result.total_tokens
            row.cost += result.cost

    def aggregate(self, group_by: str = "provider") -> list[dict]:
        cols = {
            "provider": ProviderUsage.provider_id,
            "employee": ProviderUsage.ai_employee_id,
            "project": ProviderUsage.project_id,
            "day": ProviderUsage.day,
            "month": ProviderUsage.month,
        }
        col = cols.get(group_by, ProviderUsage.provider_id)
        rows = self.db.execute(
            select(
                col,
                func.sum(ProviderUsage.total_tokens),
                func.sum(ProviderUsage.estimated_cost),
            ).group_by(col)
        ).all()
        labels = self._labels(group_by)
        return [
            {
                "key": str(k) if k is not None else None,
                "label": labels.get(k, str(k) if k is not None else "—"),
                "tokens": int(tokens or 0),
                "cost": round(cost or 0.0, 6),
            }
            for k, tokens, cost in rows
        ]

    def _labels(self, group_by: str) -> dict:
        if group_by == "provider":
            return {p.id: p.name for p in self.db.scalars(select(AIProvider)).all()}
        if group_by == "employee":
            return {e.id: e.name for e in self.db.scalars(select(AIEmployee)).all()}
        return {}


class MetricsService:
    """Latency, error, and event recording + per-provider metrics."""

    def __init__(self, db: Session, actor: str = "System"):
        self.db = db
        self.actor = actor

    def record_latency(self, provider_id, latency_ms: int, run_id=None) -> None:
        self.db.add(ProviderLatency(provider_id=provider_id, run_id=run_id, latency_ms=latency_ms))

    def record_error(self, provider_id, message: str, *, error_type="error", run_id=None) -> None:
        self.db.add(
            ProviderErrorLog(
                provider_id=provider_id, run_id=run_id, error_type=error_type, message=message
            )
        )

    def record_event(self, provider_id, event_type: str, detail: str, severity="info") -> None:
        self.db.add(
            ProviderEvent(
                provider_id=provider_id,
                event_type=event_type,
                actor=self.actor,
                detail=detail,
                severity=severity,
            )
        )

    def notify_founder(self, provider_id, detail: str) -> None:
        """Record a founder-facing notification event (surfaced on the dashboard)."""
        self.record_event(provider_id, "founder.notified", detail, severity="warning")

    def provider_metrics(self) -> list[dict]:
        providers = list(self.db.scalars(select(AIProvider).order_by(AIProvider.name)).all())
        out = []
        for p in providers:
            avg_latency = self.db.scalar(
                select(func.avg(ProviderLatency.latency_ms)).where(
                    ProviderLatency.provider_id == p.id
                )
            )
            errors = self.db.scalar(
                select(func.count(ProviderErrorLog.id)).where(ProviderErrorLog.provider_id == p.id)
            )
            tokens = self.db.scalar(
                select(func.coalesce(func.sum(ProviderUsage.total_tokens), 0)).where(
                    ProviderUsage.provider_id == p.id
                )
            )
            cost = self.db.scalar(
                select(func.coalesce(func.sum(ProviderUsage.estimated_cost), 0.0)).where(
                    ProviderUsage.provider_id == p.id
                )
            )
            out.append(
                {
                    "provider": p.name,
                    "avg_latency_ms": round(avg_latency) if avg_latency else None,
                    "errors": int(errors or 0),
                    "tokens": int(tokens or 0),
                    "cost": round(cost or 0.0, 6),
                }
            )
        return out

    def recent_events(self, limit: int = 30) -> list[dict]:
        rows = self.db.scalars(
            select(ProviderEvent).order_by(ProviderEvent.created_at.desc()).limit(limit)
        ).all()
        names = {p.id: p.name for p in self.db.scalars(select(AIProvider)).all()}
        return [
            {
                "id": str(e.id),
                "provider": names.get(e.provider_id),
                "event_type": e.event_type,
                "actor": e.actor,
                "detail": e.detail,
                "severity": e.severity,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ]


class FailoverService:
    """Resolves the ordered chain of providers to try for an execution."""

    def __init__(self, db: Session):
        self.db = db
        self.providers = ProviderService(db)

    def chain(self, primary: AIProvider) -> list[AIProvider]:
        """Primary first, then other enabled providers by ascending priority."""
        enabled = [
            p
            for p in self.db.scalars(select(AIProvider).where(AIProvider.enabled.is_(True))).all()
            if p.id != primary.id
        ]
        enabled.sort(key=lambda p: (p.priority, p.name))
        return [primary, *enabled]


class HealthMonitor:
    """Tests connectivity across providers and records health + events."""

    def __init__(self, db: Session, actor: str = "System"):
        self.db = db
        self.providers = ProviderService(db, actor=actor)

    def monitor_all(self) -> list[dict]:
        results = []
        for p in self.providers.list_providers():
            results.append(self.providers.test_connection(p.id))
        return results


class PlatformDashboard:
    """Founder + AI provider-platform dashboards."""

    def __init__(self, db: Session):
        self.db = db
        self.providers = ProviderService(db)
        self.metrics = MetricsService(db)
        self.budget = BudgetService(db)
        self.cost = CostEngine(db)

    def founder(self) -> dict:
        runs = list(self.db.scalars(select(ExecutionRun)).all())

        def status_of(r):
            return r.status.value if hasattr(r.status, "value") else r.status

        durations = [r.duration_ms for r in runs if r.duration_ms is not None]
        return {
            "providers": [
                {
                    "name": p["name"],
                    "enabled": p["enabled"],
                    "is_default": p["is_default"],
                    "health": p["health"],
                    "active_model": p["active_model"],
                    "has_secret": p["has_secret"],
                    "priority": p["priority"],
                }
                for p in (self.providers.serialize(x) for x in self.providers.list_providers())
            ],
            "running_executions": sum(1 for r in runs if status_of(r) == "running"),
            "failed_executions": sum(1 for r in runs if status_of(r) == "failed"),
            "completed_executions": sum(1 for r in runs if status_of(r) == "completed"),
            "token_usage": self.db.scalar(
                select(func.coalesce(func.sum(ProviderUsage.total_tokens), 0))
            )
            or 0,
            "estimated_cost": round(
                self.db.scalar(select(func.coalesce(func.sum(ProviderUsage.estimated_cost), 0.0)))
                or 0.0,
                6,
            ),
            "avg_latency_ms": round(sum(durations) / len(durations)) if durations else None,
            "budget": self.budget.status(),
            "metrics": self.metrics.provider_metrics(),
            "recent_events": self.metrics.recent_events(10),
            "cost_by_provider": self.cost.aggregate("provider"),
        }

    def ai(self, employee_id: uuid.UUID) -> dict:
        employee = self.db.get(AIEmployee, employee_id)
        if employee is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(f"AI employee {employee_id} not found")
        provider = self.providers.provider_for_employee(employee)
        last = self.db.scalar(
            select(ExecutionRun)
            .where(ExecutionRun.ai_employee_id == employee_id)
            .order_by(ExecutionRun.created_at.desc())
        )
        tokens = self.db.scalar(
            select(func.coalesce(func.sum(ProviderUsage.total_tokens), 0)).where(
                ProviderUsage.ai_employee_id == employee_id
            )
        )
        cost = self.db.scalar(
            select(func.coalesce(func.sum(ProviderUsage.estimated_cost), 0.0)).where(
                ProviderUsage.ai_employee_id == employee_id
            )
        )
        return {
            "employee": {"id": str(employee.id), "name": employee.name},
            "current_provider": provider.name,
            "current_model": provider.active_model or provider.default_model,
            "execution_status": (
                (last.status.value if hasattr(last.status, "value") else last.status)
                if last
                else None
            ),
            "last_response": last.output if last else None,
            "response_time_ms": last.duration_ms if last else None,
            "tokens": int(tokens or 0),
            "cost": round(cost or 0.0, 6),
        }
