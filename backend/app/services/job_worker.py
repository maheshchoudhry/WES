"""Durable job worker (WP3, Phase 2).

Claims jobs from the DB-backed queue and runs their registered handler. Designed
to be both:

* **deterministic for tests** — ``run_once`` claims and executes exactly one job in
  the caller's control (no threads), and
* **a real background runner** — ``JobWorker.start`` spawns a daemon thread that
  recovers orphaned jobs on startup and then polls-and-executes continuously.

Each job runs in its own session. The claim is committed before the handler runs,
so a crash mid-handler leaves the job ``running`` with a stale heartbeat — which
``recover_orphans`` re-queues on the next startup (resume-after-restart).
"""

from __future__ import annotations

import json
import threading
import uuid
from collections.abc import Callable
from typing import Any

from app.models.jobs import Job
from app.services.job_queue import JobQueue

# handler(db, payload, job, queue) -> result dict. Raise to fail the job.
Handler = Callable[[Any, dict, Job, JobQueue], Any]
JOB_HANDLERS: dict[str, Handler] = {}


def register_handler(job_type: str, handler: Handler) -> None:
    JOB_HANDLERS[job_type] = handler


def run_once(session_factory, worker_id: str = "worker-1") -> bool:
    """Claim and execute at most one job. Returns True if a job was handled."""
    db = session_factory()
    try:
        queue = JobQueue(db)
        job = queue.claim_next(worker_id)
        if job is None:
            return False
        db.commit()  # persist the claim before running the handler
        job_id = job.id
        handler = JOB_HANDLERS.get(job.job_type)
        try:
            if handler is None:
                raise RuntimeError(f"no handler registered for job_type '{job.job_type}'")
            payload = json.loads(job.payload or "{}")
            result = handler(db, payload, job, queue)
            queue.complete(job, result if isinstance(result, dict) else {"value": result})
            db.commit()
        except Exception as exc:  # noqa: BLE001 - queue records the failure
            db.rollback()
            fresh = db.get(Job, job_id)
            if fresh is not None:
                JobQueue(db).fail(fresh, f"{type(exc).__name__}: {exc}")
                db.commit()
        return True
    finally:
        db.close()


class JobWorker:
    def __init__(
        self,
        session_factory,
        *,
        worker_id: str = "worker-1",
        poll_interval: float = 0.5,
        stale_seconds: int = 120,
    ):
        self.session_factory = session_factory
        self.worker_id = worker_id
        self.poll_interval = poll_interval
        self.stale_seconds = stale_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def recover(self) -> int:
        db = self.session_factory()
        try:
            n = JobQueue(db).recover_orphans(self.stale_seconds)
            db.commit()
            return n
        finally:
            db.close()

    def start(self) -> None:
        self.recover()  # resume anything a previous run left behind
        self._thread = threading.Thread(target=self._loop, daemon=True, name="wes-job-worker")
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                did_work = run_once(self.session_factory, self.worker_id)
            except Exception:  # noqa: BLE001 - never let the loop die
                did_work = False
            if not did_work:
                self._stop.wait(self.poll_interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)


# -- built-in handlers -------------------------------------------------------


def _development_workflow(db, payload: dict, job: Job, queue: JobQueue) -> dict:
    """Run the full autonomous development workflow for a task, durably. On PR-ready
    the Founder is notified that an approval is required."""
    from app.services.development_service import DevelopmentService
    from app.services.notifications import NotificationService

    task_id = uuid.UUID(payload["task_id"])
    queue.heartbeat(job, progress_pct=10, message="running development workflow")
    db.commit()
    result = DevelopmentService(db).run_workflow(task_id, payload.get("provider_name"))
    status = result.get("status")
    if status == "pr_ready":
        NotificationService(db).create(
            kind="approval_needed",
            title=f"{result.get('code', 'Task')} awaits your approval",
            message=f"{result.get('title', 'A task')} reached PR — Founder approval required.",
            severity="action",
            entity_type="dev_task",
            entity_id=str(task_id),
        )
    return {"task_id": str(task_id), "status": status}


def _project_execution(db, payload: dict, job: Job, queue: JobQueue) -> dict:
    """Autonomous project execution: turn each approved-plan work item into a
    development task and enqueue its durable workflow."""
    from sqlalchemy import select

    from app.domain.work_enums import WorkStatus
    from app.models.work import WorkItem
    from app.services.development_service import DevelopmentService
    from app.services.notifications import NotificationService

    project_id = uuid.UUID(payload["project_id"])
    svc = DevelopmentService(db)
    items = db.scalars(
        select(WorkItem).where(
            WorkItem.project_id == project_id, WorkItem.status == WorkStatus.BACKLOG
        )
    ).all()
    created = 0
    for wi in items:
        task = svc.create_task(
            wi.title,
            description=wi.description,
            work_item_id=wi.id,
            ai_employee_id=wi.assigned_ai_employee_id,
        )
        wi.status = WorkStatus.IN_PROGRESS
        db.flush()
        queue.enqueue(
            "development_workflow",
            {"task_id": str(task.id)},
            idempotency_key=f"dev-workflow:{task.id}",
        )
        created += 1
    NotificationService(db).create(
        kind="project_execution",
        title="Autonomous project execution started",
        message=f"{created} tasks queued for development.",
        entity_type="project",
        entity_id=str(project_id),
    )
    return {"tasks_created": created}


def _devops_pipeline(db, payload: dict, job: Job, queue: JobQueue) -> dict:
    """Run the CI/CD pipeline (build → test → scan → stage deploy → monitor) for an
    approved task, then notify the Founder that deployment completed."""
    from app.services.devops_pipeline import PipelineService
    from app.services.notifications import NotificationService

    task_id = uuid.UUID(payload["task_id"])
    environment = payload.get("environment", "staging")
    queue.heartbeat(job, progress_pct=10, message=f"running pipeline → {environment}")
    db.commit()
    pipe = PipelineService(db).run(task_id, environment)
    status = pipe.status.value if hasattr(pipe.status, "value") else pipe.status
    NotificationService(db).create(
        kind="deployment",
        title=f"Deployment to {environment} complete",
        message=f"Pipeline {pipe.code} finished ({status}).",
        severity="info",
        entity_type="dev_task",
        entity_id=str(task_id),
    )
    return {"pipeline": pipe.code, "status": status}


register_handler("development_workflow", _development_workflow)
register_handler("project_execution", _project_execution)
register_handler("devops_pipeline", _devops_pipeline)
