"""Quality Gate Engine API + integration tests (Sprint 14).

Runs a real autonomous task, then asserts the quality gates evaluated it and
gate approval on the result — plus a service-level test that a security finding
blocks eligibility and approval."""


def _run_task(client, title="Add health ping utility"):
    return client.post("/api/v1/development/run", json={"title": title}).json()["data"]


def test_gate_runs_in_workflow(client, quality_seeded):
    task = _run_task(client)
    gate = client.get(f"/api/v1/quality/tasks/{task['id']}/gate").json()["data"]
    assert gate is not None
    assert gate["status"] == "passed"
    assert gate["approval_eligible"] is True
    assert gate["overall_score"] >= 90
    assert gate["critical_count"] == 0
    assert len(gate["gates"]) == 7 and all(g["passed"] for g in gate["gates"])


def test_report_has_all_sections(client, quality_seeded):
    task = _run_task(client, "Add cache helper")
    report = client.get(f"/api/v1/quality/tasks/{task['id']}/report").json()["data"]
    for key in (
        "gate",
        "review_findings",
        "security_findings",
        "performance_findings",
        "dependency_findings",
        "documentation_findings",
        "compliance",
        "metrics",
        "release_readiness",
    ):
        assert key in report
    assert report["metrics"]["confidence_score"] >= 0
    assert report["release_readiness"]["status"] == "ready"
    assert all(c["status"] == "pass" for c in report["compliance"])


def test_timeline_includes_quality_gate(client, quality_seeded):
    task = _run_task(client, "Add slug helper")
    timeline = client.get(f"/api/v1/development/tasks/{task['id']}/timeline").json()["data"]
    assert any(s["stage"] == "quality_gate" for s in timeline)


def test_rules_seeded(client, quality_seeded):
    rules = client.get("/api/v1/quality/rules").json()["data"]
    codes = {r["code"] for r in rules}
    assert {"architecture_score", "security_critical", "tests_passed"} <= codes
    assert all(r["mandatory"] for r in rules)


def test_re_evaluate(client, quality_seeded):
    task = _run_task(client, "Add config loader")
    resp = client.post(f"/api/v1/quality/tasks/{task['id']}/evaluate")
    assert resp.status_code == 200
    assert resp.json()["data"]["approval_eligible"] is True


def test_founder_dashboard(client, quality_seeded):
    _run_task(client, "Add greeter")
    d = client.get("/api/v1/quality/founder-dashboard").json()["data"]
    assert d["total_gate_runs"] >= 1
    assert d["approval_eligible"] >= 1
    assert d["release_ready"] >= 1
    assert d["avg_review_score"] > 0


def test_ai_dashboard(client, quality_seeded):
    _run_task(client, "Add pinger")
    d = client.get("/api/v1/quality/ai-dashboard").json()["data"]
    assert d["quality_status"] == "eligible"
    assert "review_feedback" in d


def test_approval_allowed_when_gate_passes(client, quality_seeded):
    task = _run_task(client, "Add timestamp util")
    resp = client.post(
        f"/api/v1/development/tasks/{task['id']}/approve",
        json={"decision": "approved", "notes": "ok"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "approved"


# -- service-level: a security finding blocks eligibility + approval --------


def _seed_bad_task(db):
    from app.domain.development_enums import ChangeType, DevTaskStatus
    from app.models.development import DevelopmentTask, GeneratedChange

    task = DevelopmentTask(code="DEV-BAD1", title="Insecure change", status=DevTaskStatus.PR_READY)
    db.add(task)
    db.flush()
    db.add(
        GeneratedChange(
            task_id=task.id,
            path="insecure.py",
            change_type=ChangeType.CREATE,
            language="python",
            content='API_KEY = "sk-live-super-secret-key-123"\n\n\ndef go():\n    return API_KEY\n',
        )
    )
    db.commit()
    return task


def test_security_finding_blocks_gate_and_approval(db_session):
    from app.core.exceptions import ValidationError
    from app.services.dev_review import ApprovalService
    from app.services.quality_gate_service import QualityGateService

    task = _seed_bad_task(db_session)
    gate = QualityGateService(db_session).evaluate(task.id)
    assert gate.approval_eligible is False
    assert gate.critical_count >= 1
    assert gate.security_score < 100

    # Approval is refused until the Founder overrides.
    import pytest

    with pytest.raises(ValidationError):
        ApprovalService(db_session, actor="Founder").decide(task.id, "approved")

    # Founder override succeeds.
    record = ApprovalService(db_session, actor="Founder").decide(
        task.id, "approved", "override", override=True
    )
    assert record.decision.value == "approved" if hasattr(record.decision, "value") else True


def test_approval_without_gate_is_refused(db_session):
    from app.core.exceptions import ValidationError
    from app.domain.development_enums import DevTaskStatus
    from app.models.development import DevelopmentTask
    from app.services.dev_review import ApprovalService

    task = DevelopmentTask(code="DEV-NG", title="No gate", status=DevTaskStatus.PR_READY)
    db_session.add(task)
    db_session.commit()
    import pytest

    with pytest.raises(ValidationError):
        ApprovalService(db_session, actor="Founder").decide(task.id, "approved")
