"""Enterprise DevOps Platform API + integration tests (Sprint 15).

Runs the REAL CI/CD pipeline (build → tests → security → artifact → release →
staging deploy → monitoring), then the Founder-gated production deployment and a
rollback — all against real local artifacts and deployment directories."""

import glob
import os


def _approved_task(client, title="Add health ping utility"):
    task = client.post("/api/v1/development/run", json={"title": title}).json()["data"]
    client.post(
        f"/api/v1/development/tasks/{task['id']}/approve",
        json={"decision": "approved", "notes": "ok"},
    )
    return task


def _run_pipeline(client, task, environment="staging"):
    return client.post(
        "/api/v1/devops/pipelines/run",
        json={"task_id": task["id"], "environment": environment},
    ).json()["data"]


def test_pipeline_requires_approved_task(client, devops_seeded):
    # A task that ran but was NOT approved cannot enter the pipeline.
    task = client.post("/api/v1/development/run", json={"title": "Unapproved change"}).json()[
        "data"
    ]
    resp = client.post(
        "/api/v1/devops/pipelines/run", json={"task_id": task["id"], "environment": "staging"}
    )
    assert resp.status_code == 422


def test_full_pipeline_executes(client, devops_seeded):
    task = _approved_task(client)
    pipe = _run_pipeline(client, task)
    assert pipe["status"] == "awaiting_production"
    stages = {s["stage"]: s["status"] for s in pipe["stages"]}
    assert stages["build"] == "passed"
    assert stages["unit_tests"] == "passed"
    assert stages["security_scan"] == "passed"
    assert stages["staging_deploy"] == "passed"
    assert stages["monitoring"] == "passed"
    assert stages["production_approval"] == "pending"
    assert pipe["release"]["version"].startswith("0.5.0-beta")
    assert pipe["build"]["checksum"]  # real sha256


def test_artifact_and_deployment_are_real(client, devops_seeded):
    task = _approved_task(client, "Add cache helper")
    pipe = _run_pipeline(client, task)
    # A staging deployment really extracted files to disk.
    deploys = client.get("/api/v1/devops/deployments?environment=staging").json()["data"]
    deployed = next(d for d in deploys if d["version"] == pipe["release"]["version"])
    assert deployed["status"] == "deployed"
    assert deployed["path"] and os.path.isdir(deployed["path"])
    assert glob.glob(os.path.join(deployed["path"], "**", "*.py"), recursive=True)


def test_production_requires_founder_approval(client, devops_seeded):
    task = _approved_task(client, "Add config loader")
    pipe = _run_pipeline(client, task)
    # No production deployment exists yet.
    prod = client.get("/api/v1/devops/deployments?environment=production").json()["data"]
    assert all(p["version"] != pipe["release"]["version"] for p in prod)
    # Founder approves production.
    resp = client.post(f"/api/v1/devops/pipelines/{pipe['id']}/deploy-production")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "passed"
    assert any(
        d["environment"] == "production" and d["status"] == "deployed" for d in data["deployments"]
    )


def test_releases_and_notes(client, devops_seeded):
    task = _approved_task(client, "Add slug helper")
    _run_pipeline(client, task)
    releases = client.get("/api/v1/devops/releases").json()["data"]
    assert len(releases) >= 1
    r = releases[0]
    assert r["version"].startswith("0.5.0-beta")
    assert r["notes"] and r["notes"]["title"].startswith("Release")


def test_environments_seeded(client, devops_seeded):
    envs = client.get("/api/v1/devops/environments").json()["data"]
    names = {e["name"] for e in envs}
    assert {"development", "testing", "staging", "production"} == names
    prod = next(e for e in envs if e["name"] == "production")
    assert prod["requires_approval"] is True


def test_rollback(client, devops_seeded):
    task = _approved_task(client, "Add greeter")
    pipe = _run_pipeline(client, task)
    release_id = pipe["release"]["id"]
    resp = client.post(
        "/api/v1/devops/rollback",
        json={"environment": "staging", "to_release_id": release_id, "reason": "revert"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "completed"
    history = client.get("/api/v1/devops/rollback-history").json()["data"]
    assert any(h["environment"] == "staging" for h in history)


def test_monitoring_snapshot_and_health(client, devops_seeded):
    snap = client.post("/api/v1/devops/monitoring/snapshot").json()["data"]
    assert snap["overall_status"] in ("healthy", "degraded", "down")
    assert 0 <= snap["cpu_pct"] <= 100
    assert snap["db_status"] == "healthy"
    health = client.get("/api/v1/devops/monitoring/health").json()["data"]
    assert health is not None
    events = client.get("/api/v1/devops/monitoring/events").json()["data"]
    assert any(e["category"] == "system" for e in events)


def test_founder_dashboard(client, devops_seeded):
    task = _approved_task(client, "Add util one")
    _run_pipeline(client, task)
    d = client.get("/api/v1/devops/founder-dashboard").json()["data"]
    assert d["total_pipelines"] >= 1
    assert d["awaiting_production"] >= 1
    assert d["releases"] >= 1
    assert d["system_health"] is not None


def test_ai_dashboard(client, devops_seeded):
    task = _approved_task(client, "Add util two")
    _run_pipeline(client, task)
    d = client.get("/api/v1/devops/ai-dashboard").json()["data"]
    assert d["pipeline"] is not None
    assert d["pipeline_progress"]


def test_incident_lifecycle(db_session):
    """A monitoring breach generates an incident that can be resolved."""
    from app.services.devops_monitor import IncidentService

    svc = IncidentService(db_session)
    inc = svc.generate("Test incident", "critical", source="test", recovery_action="fix it")
    assert inc.code.startswith("INC-")
    resolved = svc.resolve(inc.id)
    assert (
        resolved.status.value if hasattr(resolved.status, "value") else resolved.status
    ) == "resolved"
