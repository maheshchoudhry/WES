"""Durable job queue endpoints (WP3, Phase 2).

Inspect and control background jobs. Reuses the Development RBAC scopes:
``dev:read`` to view, ``dev:execute`` to control (cancel/retry/pause/resume).
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.domain.roles import Permission
from app.services.job_queue import JobQueue

router = APIRouter(prefix="/jobs", tags=["jobs"])
_read = Depends(require_permission(Permission.DEV_READ))
_execute = Depends(require_permission(Permission.DEV_EXECUTE))


@router.get("", dependencies=[_read])
def list_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> dict:
    items = JobQueue(db).list_jobs(status=status_filter)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{job_id}", dependencies=[_read])
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return {"data": JobQueue(db).get(job_id)}


@router.post("/{job_id}/cancel", dependencies=[_execute])
def cancel_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return {"data": JobQueue(db).serialize(JobQueue(db).cancel(job_id))}


@router.post("/{job_id}/retry", dependencies=[_execute])
def retry_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return {"data": JobQueue(db).serialize(JobQueue(db).retry(job_id))}


@router.post("/{job_id}/pause", dependencies=[_execute])
def pause_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return {"data": JobQueue(db).serialize(JobQueue(db).pause(job_id))}


@router.post("/{job_id}/resume", dependencies=[_execute])
def resume_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return {"data": JobQueue(db).serialize(JobQueue(db).resume(job_id))}
