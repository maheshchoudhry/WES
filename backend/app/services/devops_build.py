"""Build & Artifact services for the DevOps Platform (Sprint 15).

Builds a real implementation from its Sprint-13 git sandbox: compiles the code
(``py_compile``), packages a real tarball artifact with a sha256 checksum, and —
when enabled and Docker is available — builds a real Docker image. Everything is
performed under the configured DevOps workspace; never a real production host.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.devops_enums import ArtifactKind, BuildStatus
from app.models.development import DevelopmentTask
from app.models.devops import BuildRun, DeploymentArtifact

_IGNORE = {".git", "__pycache__", ".pytest_cache", "node_modules", ".mypy_cache"}


def workspace_base() -> str:
    base = os.path.abspath(get_settings().devops_workspace_dir)
    os.makedirs(base, exist_ok=True)
    return base


def artifacts_dir() -> str:
    d = os.path.join(workspace_base(), "artifacts")
    os.makedirs(d, exist_ok=True)
    return d


def deployments_dir(environment: str) -> str:
    d = os.path.join(workspace_base(), "deployments", environment)
    os.makedirs(d, exist_ok=True)
    return d


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _docker_available() -> bool:
    if not get_settings().devops_docker_builds:
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=20).returncode == 0
    except Exception:
        return False


class ArtifactService:
    def __init__(self, db: Session):
        self.db = db

    def package(
        self, sandbox: str, name: str, *, build_run_id=None, release_version_id=None
    ) -> DeploymentArtifact:
        """Create a real .tar.gz of the sandbox (excluding VCS/build dirs) + checksum."""
        dest = os.path.join(artifacts_dir(), f"{name}.tar.gz")

        def _filter(tarinfo):
            parts = tarinfo.name.split("/")
            if any(p in _IGNORE for p in parts):
                return None
            return tarinfo

        with tarfile.open(dest, "w:gz") as tar:
            tar.add(sandbox, arcname=name, filter=_filter)
        checksum = sha256_of(dest)
        size = os.path.getsize(dest)
        artifact = DeploymentArtifact(
            build_run_id=build_run_id,
            release_version_id=release_version_id,
            name=f"{name}.tar.gz",
            kind=ArtifactKind.TARBALL.value,
            path=dest,
            checksum=checksum,
            size_bytes=size,
            artifact_metadata=json.dumps({"format": "tar.gz", "source": "sandbox"}),
        )
        self.db.add(artifact)
        self.db.flush()
        return artifact

    def build_image(
        self, sandbox: str, tag: str, *, release_version_id=None
    ) -> DeploymentArtifact | None:
        """Build a REAL Docker image when enabled + available; else return None."""
        if not _docker_available():
            return None
        dockerfile = os.path.join(sandbox, "Dockerfile")
        if not os.path.exists(dockerfile):
            with open(dockerfile, "w", encoding="utf-8") as fh:
                fh.write(
                    "FROM python:3.13-slim\nWORKDIR /app\nCOPY . .\n"
                    'CMD ["python", "-c", "print(\'wes artifact ok\')"]\n'
                )
        try:
            proc = subprocess.run(
                ["docker", "build", "-q", "-t", tag, sandbox],
                capture_output=True,
                text=True,
                timeout=600,
            )
        except Exception:
            return None
        if proc.returncode != 0:
            return None
        digest = (proc.stdout or "").strip()
        artifact = DeploymentArtifact(
            release_version_id=release_version_id,
            name=tag,
            kind=ArtifactKind.DOCKER_IMAGE.value,
            image_tag=tag,
            checksum=digest.replace("sha256:", "")[:64] if digest else None,
            artifact_metadata=json.dumps({"engine": "docker", "digest": digest}),
        )
        self.db.add(artifact)
        self.db.flush()
        return artifact

    def list_artifacts(self, limit: int = 100) -> list[DeploymentArtifact]:
        return list(
            self.db.scalars(
                select(DeploymentArtifact)
                .order_by(DeploymentArtifact.created_at.desc())
                .limit(limit)
            ).all()
        )


class BuildService:
    def __init__(self, db: Session):
        self.db = db

    def build(
        self, task: DevelopmentTask, *, pipeline_run_id=None
    ) -> tuple[BuildRun, DeploymentArtifact | None]:
        started = time.monotonic()
        sandbox = task.sandbox_path
        commands = ["python -m py_compile <sources>", "tar czf artifact"]
        build = BuildRun(
            task_id=task.id,
            pipeline_run_id=pipeline_run_id,
            status=BuildStatus.BUILDING,
            language="python",
            commands=json.dumps(commands),
        )
        self.db.add(build)
        self.db.flush()

        if not sandbox or not os.path.isdir(sandbox):
            build.status = BuildStatus.FAILED
            build.output = "Sandbox not found — nothing to build."
            self.db.flush()
            return build, None

        py_files = [
            p
            for p in glob.glob(os.path.join(sandbox, "**", "*.py"), recursive=True)
            if "__pycache__" not in p
        ]
        output_lines = []
        rc = 0
        if py_files:
            proc = subprocess.run(
                [sys.executable, "-m", "py_compile", *py_files],
                cwd=sandbox,
                capture_output=True,
                text=True,
                timeout=120,
            )
            rc = proc.returncode
            output_lines.append((proc.stdout or "") + (proc.stderr or ""))
        if rc != 0:
            build.status = BuildStatus.FAILED
            build.output = "\n".join(output_lines)[:4000]
            build.duration_ms = int((time.monotonic() - started) * 1000)
            self.db.flush()
            return build, None

        artifact = ArtifactService(self.db).package(
            sandbox, f"build-{build.id.hex[:10]}", build_run_id=build.id
        )
        build.status = BuildStatus.SUCCESS
        build.checksum = artifact.checksum
        build.output = f"Compiled {len(py_files)} files; artifact {artifact.name} ({artifact.size_bytes} bytes)."
        build.duration_ms = int((time.monotonic() - started) * 1000)
        self.db.flush()
        return build, artifact


def extract_artifact(artifact_path: str, dest_dir: str) -> str:
    """Extract a tarball artifact into a real deployment directory (returns it)."""
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir, ignore_errors=True)
    os.makedirs(dest_dir, exist_ok=True)
    with tarfile.open(artifact_path, "r:gz") as tar:
        tar.extractall(dest_dir)  # noqa: S202 - artifacts are engine-produced, sandboxed
    return dest_dir


def verify_deployment(dest_dir: str) -> bool:
    """Verify a deployment by compiling its Python files (real check)."""
    py_files = [
        p
        for p in glob.glob(os.path.join(dest_dir, "**", "*.py"), recursive=True)
        if "__pycache__" not in p
    ]
    if not py_files:
        return True
    proc = subprocess.run(
        [sys.executable, "-m", "py_compile", *py_files],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode == 0
