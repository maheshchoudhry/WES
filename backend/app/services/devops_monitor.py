"""Monitoring, Health & Incident services (Sprint 15).

Captures REAL system health (CPU/memory/disk via psutil) plus application, API,
database, AI-provider, and execution-queue health, records monitoring events and
system-health snapshots, and generates incidents (with recovery actions) when a
metric breaches its threshold.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.devops_enums import HealthStatus, IncidentSeverity, IncidentStatus
from app.models.devops import IncidentReport, MonitoringEvent, SystemHealth

_CPU_WARN, _MEM_WARN, _DISK_WARN = 85.0, 85.0, 90.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _system_metrics() -> dict:
    try:
        import psutil

        return {
            "cpu": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
        }
    except Exception:  # pragma: no cover - psutil always present in this build
        import os

        try:
            load = os.getloadavg()[0]
        except OSError:
            load = 0.0
        return {"cpu": min(100.0, load * 10), "memory": 0.0, "disk": 0.0}


class IncidentService:
    def __init__(self, db: Session, actor: str = "Monitoring"):
        self.db = db
        self.actor = actor

    def _next_code(self) -> str:
        n = self.db.scalar(select(func.count(IncidentReport.id))) or 0
        return f"INC-{n + 1:04d}"

    def generate(
        self,
        title: str,
        severity: IncidentSeverity | str,
        *,
        source: str = "monitoring",
        detail: str | None = None,
        recovery_action: str | None = None,
        deployment_run_id=None,
    ) -> IncidentReport:
        inc = IncidentReport(
            code=self._next_code(),
            title=title,
            severity=severity.value if isinstance(severity, IncidentSeverity) else severity,
            status=IncidentStatus.OPEN,
            source=source,
            detail=detail,
            recovery_action=recovery_action,
            deployment_run_id=deployment_run_id,
        )
        self.db.add(inc)
        self.db.flush()
        return inc

    def resolve(self, incident_id: uuid.UUID) -> IncidentReport:
        inc = self.db.get(IncidentReport, incident_id)
        if inc is None:
            raise NotFoundError(f"Incident {incident_id} not found")
        inc.status = IncidentStatus.RESOLVED
        inc.resolved_at = _now()
        self.db.flush()
        return inc

    def list_incidents(self, *, status: str | None = None, limit: int = 50) -> list[dict]:
        stmt = select(IncidentReport).order_by(IncidentReport.created_at.desc()).limit(limit)
        if status:
            stmt = (
                select(IncidentReport)
                .where(IncidentReport.status == status)
                .order_by(IncidentReport.created_at.desc())
                .limit(limit)
            )
        return [self.serialize(i) for i in self.db.scalars(stmt).all()]

    def serialize(self, i: IncidentReport) -> dict:
        return {
            "id": str(i.id),
            "code": i.code,
            "title": i.title,
            "severity": i.severity.value if hasattr(i.severity, "value") else i.severity,
            "status": i.status.value if hasattr(i.status, "value") else i.status,
            "source": i.source,
            "detail": i.detail,
            "recovery_action": i.recovery_action,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }


class MonitoringService:
    def __init__(self, db: Session):
        self.db = db

    def _event(self, category, metric, value, unit, status, detail=None) -> None:
        self.db.add(
            MonitoringEvent(
                category=category,
                metric=metric,
                value=value,
                unit=unit,
                status=status,
                detail=detail,
            )
        )

    def recent_events(self, limit: int = 40) -> list[dict]:
        rows = self.db.scalars(
            select(MonitoringEvent).order_by(MonitoringEvent.created_at.desc()).limit(limit)
        ).all()
        return [
            {
                "category": e.category,
                "metric": e.metric,
                "value": e.value,
                "unit": e.unit,
                "status": e.status.value if hasattr(e.status, "value") else e.status,
                "detail": e.detail,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ]


class HealthService:
    """Captures a real system-health snapshot and raises incidents on breaches."""

    def __init__(self, db: Session):
        self.db = db
        self.monitor = MonitoringService(db)

    def _db_health(self) -> tuple[str, int]:
        from app.models.employee import Employee

        started = time.monotonic()
        try:
            self.db.scalar(select(func.count(Employee.id)))
            return "healthy", int((time.monotonic() - started) * 1000)
        except Exception:  # pragma: no cover - defensive
            return "down", 0

    def _provider_health(self) -> str:
        from app.models.orchestration import AIProvider, ProviderHealthRecord

        default = self.db.scalar(select(AIProvider).where(AIProvider.is_default.is_(True)))
        if default is None:
            return "degraded"
        rec = self.db.scalar(
            select(ProviderHealthRecord)
            .where(ProviderHealthRecord.provider_id == default.id)
            .order_by(ProviderHealthRecord.checked_at.desc())
        )
        if rec is None:
            return "healthy"
        s = rec.status.value if hasattr(rec.status, "value") else rec.status
        return "healthy" if s == "healthy" else "degraded"

    def _queue_depth(self) -> int:
        try:
            from app.models.execution import ExecutionQueueItem

            return self.db.scalar(select(func.count(ExecutionQueueItem.id))) or 0
        except Exception:  # pragma: no cover
            return 0

    def snapshot(self) -> SystemHealth:
        m = _system_metrics()
        db_status, response_ms = self._db_health()
        provider_status = self._provider_health()
        queue = self._queue_depth()

        degraded = (
            m["cpu"] > _CPU_WARN
            or m["memory"] > _MEM_WARN
            or m["disk"] > _DISK_WARN
            or provider_status != "healthy"
        )
        overall = (
            HealthStatus.DOWN
            if db_status == "down"
            else (HealthStatus.DEGRADED if degraded else HealthStatus.HEALTHY)
        )

        health = SystemHealth(
            overall_status=overall,
            app_status="healthy",
            api_status="healthy",
            db_status=db_status,
            provider_status=provider_status,
            cpu_pct=round(m["cpu"], 1),
            memory_pct=round(m["memory"], 1),
            disk_pct=round(m["disk"], 1),
            queue_depth=queue,
            response_time_ms=response_ms,
        )
        self.db.add(health)

        def _st(v, warn):
            return HealthStatus.DEGRADED if v > warn else HealthStatus.HEALTHY

        self.monitor._event("system", "cpu", m["cpu"], "%", _st(m["cpu"], _CPU_WARN))
        self.monitor._event("system", "memory", m["memory"], "%", _st(m["memory"], _MEM_WARN))
        self.monitor._event("system", "disk", m["disk"], "%", _st(m["disk"], _DISK_WARN))
        self.monitor._event("api", "response_time", response_ms, "ms", HealthStatus.HEALTHY)
        self.monitor._event(
            "database",
            "status",
            1.0 if db_status == "healthy" else 0.0,
            None,
            HealthStatus.HEALTHY if db_status == "healthy" else HealthStatus.DOWN,
        )
        self.monitor._event(
            "provider",
            "status",
            1.0 if provider_status == "healthy" else 0.0,
            None,
            HealthStatus.HEALTHY if provider_status == "healthy" else HealthStatus.DEGRADED,
        )
        self.monitor._event("queue", "depth", float(queue), "items", HealthStatus.HEALTHY)
        self.db.flush()

        # Raise incidents on breaches.
        incidents = IncidentService(self.db)
        if m["cpu"] > _CPU_WARN:
            incidents.generate(
                f"High CPU usage ({m['cpu']:.0f}%)",
                IncidentSeverity.WARNING,
                source="monitoring",
                detail="CPU above threshold",
                recovery_action="Scale workers or investigate hot loops.",
            )
        if m["disk"] > _DISK_WARN:
            incidents.generate(
                f"High disk usage ({m['disk']:.0f}%)",
                IncidentSeverity.CRITICAL,
                source="monitoring",
                detail="Disk above threshold",
                recovery_action="Prune artifacts and old deployments.",
            )
        if db_status == "down":
            incidents.generate(
                "Database unreachable",
                IncidentSeverity.CRITICAL,
                source="monitoring",
                recovery_action="Check the database connection and restart if needed.",
            )
        self.db.flush()
        return health

    def latest(self) -> SystemHealth | None:
        return self.db.scalar(select(SystemHealth).order_by(SystemHealth.created_at.desc()))

    def serialize(self, h: SystemHealth) -> dict:
        return {
            "overall_status": (
                h.overall_status.value if hasattr(h.overall_status, "value") else h.overall_status
            ),
            "app_status": h.app_status,
            "api_status": h.api_status,
            "db_status": h.db_status,
            "provider_status": h.provider_status,
            "cpu_pct": h.cpu_pct,
            "memory_pct": h.memory_pct,
            "disk_pct": h.disk_pct,
            "queue_depth": h.queue_depth,
            "response_time_ms": h.response_time_ms,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
