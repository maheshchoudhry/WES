"""AI Review & Quality Gate endpoints (Sprint 14).

The final engineering-validation layer over autonomous development: run/re-run the
quality gates, read the full report (findings, metrics, compliance, release
readiness), and the founder/AI dashboards. Reads: quality:read (all roles);
run/re-run: quality:review (Founder + Director)."""

import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_quality_gate_service, require_permission
from app.domain.roles import Permission

router = APIRouter(prefix="/quality", tags=["quality"])
_read = Depends(require_permission(Permission.QUALITY_READ))
_review = Depends(require_permission(Permission.QUALITY_REVIEW))


@router.get("/rules", dependencies=[_read])
def list_rules(service=Depends(get_quality_gate_service)) -> dict:
    from sqlalchemy import select

    from app.models.quality import QualityRule

    rows = service.db.scalars(select(QualityRule).order_by(QualityRule.code)).all()
    items = [
        {
            "code": r.code,
            "name": r.name,
            "category": r.category,
            "operator": r.operator,
            "threshold": r.threshold,
            "severity": r.severity.value if hasattr(r.severity, "value") else r.severity,
            "enabled": r.enabled,
            "mandatory": r.mandatory,
            "description": r.description,
        }
        for r in rows
    ]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("/tasks/{task_id}/evaluate", dependencies=[_review])
def evaluate(task_id: uuid.UUID, service=Depends(get_quality_gate_service)) -> dict:
    gate = service.evaluate(task_id)
    return {"data": service.serialize_gate(gate)}


@router.get("/tasks/{task_id}/report", dependencies=[_read])
def report(task_id: uuid.UUID, service=Depends(get_quality_gate_service)) -> dict:
    return {"data": service.report(task_id)}


@router.get("/tasks/{task_id}/gate", dependencies=[_read])
def gate(task_id: uuid.UUID, service=Depends(get_quality_gate_service)) -> dict:
    g = service.gate_for_task(task_id)
    return {"data": service.serialize_gate(g) if g else None}


@router.get("/founder-dashboard", dependencies=[_read])
def founder_dashboard(service=Depends(get_quality_gate_service)) -> dict:
    return {"data": service.founder_dashboard()}


@router.get("/ai-dashboard", dependencies=[_read])
def ai_dashboard(
    task_id: uuid.UUID | None = Query(default=None),
    service=Depends(get_quality_gate_service),
) -> dict:
    return {"data": service.ai_dashboard(task_id)}
