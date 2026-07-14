"""Release management service (Sprint 15).

Cuts a semantic release version from a passing pipeline, generates release notes
from the implementation's plan + pull-request, and tracks version/deployment
history."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.devops_enums import ReleaseStatus
from app.models.development import DevelopmentTask, GeneratedChange, PullRequest
from app.models.devops import DeploymentRun, ReleaseNote, ReleaseVersion

_BASE_VERSION = "0.5.0-beta"


class ReleaseService:
    def __init__(self, db: Session, actor: str = "DevOps Engine"):
        self.db = db
        self.actor = actor

    def _next_version(self) -> str:
        n = self.db.scalar(select(func.count(ReleaseVersion.id))) or 0
        return f"{_BASE_VERSION}.{n + 1}"

    def create(self, task: DevelopmentTask | None, pipeline_run_id=None) -> ReleaseVersion:
        version = self._next_version()
        release = ReleaseVersion(
            version=version,
            task_id=task.id if task else None,
            pipeline_run_id=pipeline_run_id,
            status=ReleaseStatus.CANDIDATE,
            channel="beta",
            created_by=self.actor,
        )
        self.db.add(release)
        self.db.flush()

        changes = (
            self.db.scalars(select(GeneratedChange).where(GeneratedChange.task_id == task.id)).all()
            if task
            else []
        )
        pr = (
            self.db.scalar(select(PullRequest).where(PullRequest.task_id == task.id))
            if task
            else None
        )
        self.db.add(
            ReleaseNote(
                release_version_id=release.id,
                title=f"Release {version}",
                summary=(pr.title if pr else (task.title if task else f"Release {version}")),
                changes=json.dumps([c.path for c in changes]),
                highlights=(pr.release_notes if pr and pr.release_notes else "Autonomous release."),
            )
        )
        self.db.flush()
        return release

    def get(self, release_id: uuid.UUID) -> ReleaseVersion | None:
        return self.db.get(ReleaseVersion, release_id)

    def mark_released(self, release: ReleaseVersion) -> None:
        release.status = ReleaseStatus.RELEASED
        self.db.flush()

    def history(self, limit: int = 50) -> list[dict]:
        rows = self.db.scalars(
            select(ReleaseVersion).order_by(ReleaseVersion.created_at.desc()).limit(limit)
        ).all()
        return [self.serialize(r) for r in rows]

    def serialize(self, r: ReleaseVersion) -> dict:
        note = self.db.scalar(select(ReleaseNote).where(ReleaseNote.release_version_id == r.id))
        deployments = self.db.scalars(
            select(DeploymentRun).where(DeploymentRun.release_version_id == r.id)
        ).all()
        return {
            "id": str(r.id),
            "version": r.version,
            "status": r.status.value if hasattr(r.status, "value") else r.status,
            "channel": r.channel,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "notes": (
                {
                    "title": note.title,
                    "summary": note.summary,
                    "changes": json.loads(note.changes) if note.changes else [],
                    "highlights": note.highlights,
                }
                if note
                else None
            ),
            "deployments": [
                {
                    "environment": d.environment,
                    "status": d.status.value if hasattr(d.status, "value") else d.status,
                }
                for d in deployments
            ],
        }
