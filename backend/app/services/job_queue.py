"""Durable job queue (WP3, Phase 2).

DB-backed queue operations: enqueue, claim, complete, fail-with-retry, cancel,
pause/resume, and crash recovery. All state is persisted, so the queue survives a
restart — ``recover_orphans`` re-queues jobs a crashed worker left ``running``.
Single-node safe: claiming uses a guarded UPDATE and checks the affected row count.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.jobs import Job, JobStatus

# Exponential backoff (seconds) between retries, indexed by attempt number.
_BACKOFF = [0, 5, 15, 60, 300]
DEFAULT_STALE_SECONDS = 120


def _now() -> datetime:
    return datetime.now(timezone.utc)


class JobQueue:
    def __init__(self, db: Session):
        self.db = db

    # -- producers ---------------------------------------------------------

    def enqueue(
        self,
        job_type: str,
        payload: dict | None = None,
        *,
        max_attempts: int = 3,
        priority: int = 0,
        idempotency_key: str | None = None,
    ) -> Job:
        if idempotency_key:
            existing = self.db.scalar(
                select(Job).where(Job.idempotency_key == idempotency_key)
            )
            if existing is not None:
                return existing  # idempotent enqueue
        job = Job(
            job_type=job_type,
            payload=json.dumps(payload or {}),
            status=JobStatus.QUEUED,
            priority=priority,
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
            scheduled_at=_now(),
        )
        self.db.add(job)
        self.db.flush()
        return job

    # -- worker-facing -----------------------------------------------------

    def claim_next(self, worker_id: str) -> Job | None:
        """Atomically claim the highest-priority due job. Returns None if none."""
        now = _now()
        candidate = self.db.scalar(
            select(Job)
            .where(
                Job.status == JobStatus.QUEUED,
                (Job.scheduled_at.is_(None)) | (Job.scheduled_at <= now),
            )
            .order_by(Job.priority.desc(), Job.created_at.asc())
            .limit(1)
        )
        if candidate is None:
            return None
        # Guarded transition: only succeeds if the row is still QUEUED.
        result = self.db.execute(
            update(Job)
            .where(Job.id == candidate.id, Job.status == JobStatus.QUEUED)
            .values(
                status=JobStatus.RUNNING,
                worker_id=worker_id,
                attempts=Job.attempts + 1,
                started_at=candidate.started_at or now,
                heartbeat_at=now,
                progress_message="running",
            )
        )
        self.db.flush()
        if result.rowcount != 1:
            return None  # lost the race
        self.db.refresh(candidate)
        return candidate

    def heartbeat(self, job: Job, *, progress_pct: int | None = None, message: str | None = None):
        job.heartbeat_at = _now()
        if progress_pct is not None:
            job.progress_pct = max(0, min(100, progress_pct))
        if message is not None:
            job.progress_message = message
        self.db.flush()

    def complete(self, job: Job, result: dict | None = None) -> Job:
        job.status = JobStatus.COMPLETED
        job.progress_pct = 100
        job.progress_message = "completed"
        job.result = json.dumps(result or {})
        job.completed_at = _now()
        self.db.flush()
        return job

    def fail(self, job: Job, error: str) -> Job:
        """Record a failure. Retries with backoff until max_attempts, then FAILED."""
        job.error = (error or "")[:2000]
        if job.attempts < job.max_attempts:
            backoff = _BACKOFF[min(job.attempts, len(_BACKOFF) - 1)]
            job.status = JobStatus.QUEUED
            job.worker_id = None
            job.scheduled_at = _now() + timedelta(seconds=backoff)
            job.progress_message = f"retry {job.attempts}/{job.max_attempts} in {backoff}s"
        else:
            job.status = JobStatus.FAILED
            job.completed_at = _now()
            job.progress_message = "failed"
        self.db.flush()
        return job

    def recover_orphans(self, stale_seconds: int = DEFAULT_STALE_SECONDS) -> int:
        """Re-queue jobs a crashed worker left RUNNING past the heartbeat window.
        This is what makes execution resumable across restarts."""
        cutoff = _now() - timedelta(seconds=stale_seconds)
        orphans = self.db.scalars(
            select(Job).where(
                Job.status == JobStatus.RUNNING,
                (Job.heartbeat_at.is_(None)) | (Job.heartbeat_at < cutoff),
            )
        ).all()
        for job in orphans:
            job.status = JobStatus.QUEUED
            job.worker_id = None
            job.scheduled_at = _now()
            job.progress_message = "recovered after restart; re-queued"
        self.db.flush()
        return len(orphans)

    # -- control -----------------------------------------------------------

    def cancel(self, job_id: uuid.UUID) -> Job:
        job = self._get(job_id)
        if job.status in JobStatus.TERMINAL:
            raise ValidationError(f"Job is already {job.status}; cannot cancel.")
        job.status = JobStatus.CANCELLED
        job.completed_at = _now()
        job.progress_message = "cancelled"
        self.db.flush()
        return job

    def pause(self, job_id: uuid.UUID) -> Job:
        job = self._get(job_id)
        if job.status != JobStatus.QUEUED:
            raise ValidationError("Only a queued job can be paused.")
        job.status = JobStatus.PAUSED
        self.db.flush()
        return job

    def resume(self, job_id: uuid.UUID) -> Job:
        job = self._get(job_id)
        if job.status != JobStatus.PAUSED:
            raise ValidationError("Only a paused job can be resumed.")
        job.status = JobStatus.QUEUED
        job.scheduled_at = _now()
        self.db.flush()
        return job

    def retry(self, job_id: uuid.UUID) -> Job:
        job = self._get(job_id)
        if job.status not in (JobStatus.FAILED, JobStatus.CANCELLED):
            raise ValidationError("Only a failed or cancelled job can be retried.")
        job.status = JobStatus.QUEUED
        job.worker_id = None
        job.error = None
        job.scheduled_at = _now()
        job.progress_message = "manual retry"
        self.db.flush()
        return job

    # -- reads -------------------------------------------------------------

    def _get(self, job_id: uuid.UUID) -> Job:
        job = self.db.get(Job, job_id)
        if job is None:
            raise NotFoundError(f"Job {job_id} not found")
        return job

    def get(self, job_id: uuid.UUID) -> dict:
        return self.serialize(self._get(job_id))

    def list_jobs(self, *, status: str | None = None, limit: int = 100) -> list[dict]:
        stmt = select(Job).order_by(Job.created_at.desc()).limit(limit)
        if status:
            stmt = (
                select(Job)
                .where(Job.status == status)
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
        return [self.serialize(j) for j in self.db.scalars(stmt).all()]

    @staticmethod
    def serialize(job: Job) -> dict:
        return {
            "id": str(job.id),
            "job_type": job.job_type,
            "status": job.status,
            "priority": job.priority,
            "attempts": job.attempts,
            "max_attempts": job.max_attempts,
            "progress_pct": job.progress_pct,
            "progress_message": job.progress_message,
            "error": job.error,
            "result": json.loads(job.result) if job.result else None,
            "worker_id": job.worker_id,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
