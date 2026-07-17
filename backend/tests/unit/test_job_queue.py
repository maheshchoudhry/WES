"""Phase 2 (WP3) — Durable Background Execution.

Proves the DB-backed queue: enqueue → worker runs → complete; retry with backoff;
cancel; pause/resume; and crash recovery (resume-after-restart) via recover_orphans.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.jobs import Job, JobStatus
from app.services.job_queue import JobQueue
from app.services.job_worker import JOB_HANDLERS, register_handler, run_once


@pytest.fixture
def factory(SessionFactory):
    return SessionFactory


def _register_test_handlers():
    calls = {"count": 0}

    def ok(db, payload, job, queue):
        calls["count"] += 1
        return {"echo": payload.get("msg"), "n": calls["count"]}

    def boom(db, payload, job, queue):
        raise RuntimeError("intentional failure")

    register_handler("test_ok", ok)
    register_handler("test_boom", boom)
    return calls


def test_enqueue_and_worker_completes(factory):
    _register_test_handlers()
    db = factory()
    job = JobQueue(db).enqueue("test_ok", {"msg": "hello"})
    db.commit()
    jid = job.id
    db.close()

    assert run_once(factory) is True  # worker claimed + ran it
    assert run_once(factory) is False  # nothing left

    db = factory()
    done = JobQueue(db).get(jid)
    assert done["status"] == JobStatus.COMPLETED
    assert done["progress_pct"] == 100
    assert done["result"]["echo"] == "hello"
    assert done["attempts"] == 1
    db.close()


def test_failure_retries_then_fails(factory):
    _register_test_handlers()
    db = factory()
    job = JobQueue(db).enqueue("test_boom", {}, max_attempts=2)
    db.commit()
    jid = job.id
    db.close()

    # First run → failure → re-queued (attempts=1 < 2). Clear backoff so it's due.
    assert run_once(factory) is True
    db = factory()
    j = db.get(Job, jid)
    assert j.status == JobStatus.QUEUED and j.attempts == 1
    j.scheduled_at = datetime.now(timezone.utc)
    db.commit()
    db.close()

    # Second run → failure → terminal FAILED (attempts=2 == max).
    assert run_once(factory) is True
    db = factory()
    j = JobQueue(db).get(jid)
    assert j["status"] == JobStatus.FAILED
    assert j["attempts"] == 2
    assert "intentional failure" in j["error"]
    db.close()


def test_cancel_prevents_execution(factory):
    _register_test_handlers()
    db = factory()
    q = JobQueue(db)
    job = q.enqueue("test_ok", {"msg": "x"})
    db.commit()
    q.cancel(job.id)
    db.commit()
    jid = job.id
    db.close()

    assert run_once(factory) is False  # cancelled job is not claimed
    db = factory()
    assert JobQueue(db).get(jid)["status"] == JobStatus.CANCELLED
    db.close()


def test_pause_resume(factory):
    _register_test_handlers()
    db = factory()
    q = JobQueue(db)
    job = q.enqueue("test_ok", {"msg": "y"})
    db.commit()
    q.pause(job.id)
    db.commit()
    jid = job.id
    db.close()

    assert run_once(factory) is False  # paused → not runnable
    db = factory()
    JobQueue(db).resume(jid)
    db.commit()
    db.close()
    assert run_once(factory) is True  # resumed → runs
    db = factory()
    assert JobQueue(db).get(jid)["status"] == JobStatus.COMPLETED
    db.close()


def test_recover_orphans_resumes_after_restart(factory):
    """A job left RUNNING by a crashed worker (stale heartbeat) is re-queued on
    recovery and then completes — durable resume-after-restart."""
    _register_test_handlers()
    db = factory()
    q = JobQueue(db)
    job = q.enqueue("test_ok", {"msg": "recover"})
    db.commit()
    # Simulate a crash mid-run: mark RUNNING with an old heartbeat.
    job.status = JobStatus.RUNNING
    job.worker_id = "dead-worker"
    job.attempts = 1
    job.heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=600)
    db.commit()
    jid = job.id
    db.close()

    # Recovery (what runs on startup) re-queues the orphan.
    db = factory()
    recovered = JobQueue(db).recover_orphans(stale_seconds=120)
    db.commit()
    assert recovered == 1
    assert JobQueue(db).get(jid)["status"] == JobStatus.QUEUED
    db.close()

    # The worker now picks it up and finishes it.
    assert run_once(factory) is True
    db = factory()
    assert JobQueue(db).get(jid)["status"] == JobStatus.COMPLETED
    db.close()


def test_idempotent_enqueue(factory):
    _register_test_handlers()
    db = factory()
    q = JobQueue(db)
    a = q.enqueue("test_ok", {"msg": "z"}, idempotency_key="k1")
    b = q.enqueue("test_ok", {"msg": "z"}, idempotency_key="k1")
    db.commit()
    assert a.id == b.id  # same key → same job, not a duplicate
    db.close()
