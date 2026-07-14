"""Environment, Deployment & Rollback services (Sprint 15).

Deployments are REAL local deployments: the built artifact is extracted into a
per-environment directory and verified by compiling it. Production is Founder-
gated. Rollback re-deploys a previous release's artifact. Nothing is deployed to
a real production host, and nothing is ever pushed or merged.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.devops_enums import (
    DeploymentStatus,
    DeployStrategy,
    Environment,
    ReleaseStatus,
    RollbackStatus,
)
from app.models.devops import (
    DeploymentArtifact,
    DeploymentRun,
    DeploymentTarget,
    EnvironmentProfile,
    ReleaseVersion,
    RollbackHistory,
)
from app.services.devops_build import deployments_dir, extract_artifact, verify_deployment


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EnvironmentService:
    def __init__(self, db: Session):
        self.db = db

    def list_environments(self) -> list[EnvironmentProfile]:
        return list(
            self.db.scalars(select(EnvironmentProfile).order_by(EnvironmentProfile.position)).all()
        )

    def get_by_name(self, name: str) -> EnvironmentProfile | None:
        return self.db.scalar(select(EnvironmentProfile).where(EnvironmentProfile.name == name))

    def target_for(self, environment: str) -> DeploymentTarget | None:
        return self.db.scalar(
            select(DeploymentTarget).where(DeploymentTarget.environment == environment)
        )

    def serialize(self, e: EnvironmentProfile) -> dict:
        return {
            "id": str(e.id),
            "name": e.name,
            "display_name": e.display_name,
            "requires_approval": e.requires_approval,
            "strategy": e.strategy.value if hasattr(e.strategy, "value") else e.strategy,
            "variables": json.loads(e.variables) if e.variables else {},
            "active": e.active,
        }


class DeploymentService:
    def __init__(self, db: Session, actor: str = "DevOps Engine"):
        self.db = db
        self.actor = actor

    def _artifact_for(self, release: ReleaseVersion) -> DeploymentArtifact | None:
        return self.db.scalar(
            select(DeploymentArtifact).where(
                DeploymentArtifact.release_version_id == release.id,
                DeploymentArtifact.kind == "tarball",
            )
        )

    def deploy(
        self,
        release: ReleaseVersion,
        environment: str,
        *,
        pipeline_run_id=None,
        approved_by: str | None = None,
    ) -> DeploymentRun:
        """Real local deployment: extract the artifact + verify. Production is gated."""
        env = EnvironmentService(self.db).get_by_name(environment)
        target = EnvironmentService(self.db).target_for(environment)
        strategy = env.strategy if env else DeployStrategy.STANDARD
        run = DeploymentRun(
            pipeline_run_id=pipeline_run_id,
            task_id=release.task_id,
            release_version_id=release.id,
            environment=environment,
            target_id=target.id if target else None,
            strategy=strategy,
            status=DeploymentStatus.DEPLOYING,
        )
        self.db.add(run)
        self.db.flush()

        # Production requires an explicit Founder approval.
        if env and env.requires_approval and not approved_by:
            run.status = DeploymentStatus.AWAITING_APPROVAL
            run.detail = "Awaiting Founder production approval."
            self.db.flush()
            return run

        started = time.monotonic()
        artifact = self._artifact_for(release)
        if artifact is None or not artifact.path or not os.path.exists(artifact.path):
            run.status = DeploymentStatus.FAILED
            run.detail = "No deployable artifact found."
            self.db.flush()
            return run

        dest = os.path.join(deployments_dir(environment), release.version)
        try:
            extract_artifact(artifact.path, dest)
            ok = verify_deployment(dest)
        except Exception as exc:  # pragma: no cover - defensive
            run.status = DeploymentStatus.FAILED
            run.detail = f"Deployment failed: {exc}"
            self.db.flush()
            return run

        run.status = DeploymentStatus.DEPLOYED if ok else DeploymentStatus.FAILED
        run.path = dest
        run.approved_by = approved_by
        run.approved_at = _now() if approved_by else None
        run.duration_ms = int((time.monotonic() - started) * 1000)
        run.detail = (
            f"Deployed {release.version} to {environment} ({strategy.value if hasattr(strategy,'value') else strategy}); verified."
            if ok
            else "Deployed but verification failed."
        )
        if ok and environment == Environment.PRODUCTION.value:
            release.status = ReleaseStatus.RELEASED
        self.db.flush()
        return run

    def approve_production(self, deployment_run_id: uuid.UUID, approved_by: str) -> DeploymentRun:
        run = self.db.get(DeploymentRun, deployment_run_id)
        if run is None:
            raise NotFoundError(f"Deployment {deployment_run_id} not found")
        if run.status != DeploymentStatus.AWAITING_APPROVAL:
            raise ValidationError("Deployment is not awaiting approval")
        release = self.db.get(ReleaseVersion, run.release_version_id)
        # Perform the real deployment now that the Founder has approved.
        approved = self.deploy(
            release, run.environment, pipeline_run_id=run.pipeline_run_id, approved_by=approved_by
        )
        run.status = DeploymentStatus.ROLLED_BACK  # superseded by the approved run
        run.detail = "Superseded by approved production deployment."
        self.db.flush()
        return approved

    def list_deployments(self, *, environment: str | None = None, limit: int = 50) -> list[dict]:
        stmt = select(DeploymentRun).order_by(DeploymentRun.created_at.desc()).limit(limit)
        if environment:
            stmt = (
                select(DeploymentRun)
                .where(DeploymentRun.environment == environment)
                .order_by(DeploymentRun.created_at.desc())
                .limit(limit)
            )
        return [self.serialize(d) for d in self.db.scalars(stmt).all()]

    def serialize_list_for_pipeline(self, pipeline_id) -> list[dict]:
        rows = self.db.scalars(
            select(DeploymentRun)
            .where(DeploymentRun.pipeline_run_id == pipeline_id)
            .order_by(DeploymentRun.created_at)
        ).all()
        return [self.serialize(d) for d in rows]

    def serialize(self, d: DeploymentRun) -> dict:
        release = (
            self.db.get(ReleaseVersion, d.release_version_id) if d.release_version_id else None
        )
        return {
            "id": str(d.id),
            "environment": d.environment,
            "status": d.status.value if hasattr(d.status, "value") else d.status,
            "strategy": d.strategy.value if hasattr(d.strategy, "value") else d.strategy,
            "version": release.version if release else None,
            "path": d.path,
            "approved_by": d.approved_by,
            "detail": d.detail,
            "duration_ms": d.duration_ms,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }


class RollbackService:
    def __init__(self, db: Session, actor: str = "Founder"):
        self.db = db
        self.actor = actor

    def rollback(
        self, environment: str, to_release_id: uuid.UUID, reason: str | None = None
    ) -> RollbackHistory:
        """Re-deploy a previous release to the environment (real local rollback)."""
        to_release = self.db.get(ReleaseVersion, to_release_id)
        if to_release is None:
            raise NotFoundError(f"Release {to_release_id} not found")
        # The current (superseded) deployment for this environment.
        current = self.db.scalar(
            select(DeploymentRun)
            .where(
                DeploymentRun.environment == environment,
                DeploymentRun.status == DeploymentStatus.DEPLOYED,
            )
            .order_by(DeploymentRun.created_at.desc())
        )
        from_release_id = current.release_version_id if current else None

        history = RollbackHistory(
            environment=environment,
            deployment_run_id=current.id if current else None,
            from_release_id=from_release_id,
            to_release_id=to_release_id,
            status=RollbackStatus.PENDING,
            reason=reason,
            actor=self.actor,
        )
        self.db.add(history)
        self.db.flush()

        # Real rollback: redeploy the target release's artifact.
        run = DeploymentService(self.db, actor=self.actor).deploy(
            to_release, environment, approved_by=self.actor
        )
        if current is not None:
            current.status = DeploymentStatus.ROLLED_BACK
        history.status = (
            RollbackStatus.COMPLETED
            if run.status == DeploymentStatus.DEPLOYED
            else RollbackStatus.FAILED
        )
        if to_release.status == ReleaseStatus.ROLLED_BACK:
            to_release.status = ReleaseStatus.RELEASED
        self.db.flush()
        return history

    def history(self, limit: int = 50) -> list[dict]:
        rows = self.db.scalars(
            select(RollbackHistory).order_by(RollbackHistory.created_at.desc()).limit(limit)
        ).all()
        versions = {r.id: r.version for r in self.db.scalars(select(ReleaseVersion)).all()}
        return [
            {
                "id": str(h.id),
                "environment": h.environment,
                "status": h.status.value if hasattr(h.status, "value") else h.status,
                "from_version": versions.get(h.from_release_id),
                "to_version": versions.get(h.to_release_id),
                "reason": h.reason,
                "actor": h.actor,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in rows
        ]
