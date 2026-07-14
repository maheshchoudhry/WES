"""Autonomous Development Engine API + integration tests (Sprint 13).

Runs the REAL end-to-end workflow (plan → generate → modify → test → review →
document → git branch + commits → PR draft → approval) against a git sandbox."""


def _run_task(client, title="Add health ping utility"):
    resp = client.post(
        "/api/v1/development/run",
        json={"payload": {"title": title}} if False else {"title": title},
    )
    return resp


def test_full_workflow_executes(client, dev_seeded):
    resp = client.post("/api/v1/development/run", json={"title": "Add health ping utility"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["status"] == "pr_ready"
    assert data["branch_name"].startswith("feature/auto-dev-")


def test_plan_generated_from_repo_and_knowledge(client, dev_seeded):
    tid = client.post(
        "/api/v1/development/run", json={"title": "Refactor provider execute path"}
    ).json()["data"]["id"]
    full = client.get(f"/api/v1/development/tasks/{tid}").json()["data"]
    plan = full["plan"]
    assert len(plan["implementation_order"]) == 10
    assert plan["architecture_context"]  # from Repository Intelligence
    assert plan["risk_analysis"]
    assert plan["acceptance_criteria"]


def test_changes_generated_and_applied(client, dev_seeded):
    tid = client.post("/api/v1/development/run", json={"title": "Add cache helper"}).json()["data"][
        "id"
    ]
    changes = client.get(f"/api/v1/development/tasks/{tid}").json()["data"]["changes"]
    assert len(changes) == 3
    assert all(c["status"] == "applied" for c in changes)
    assert any(c["path"].endswith(".py") and not c["path"].startswith("test_") for c in changes)
    assert any(c["path"].startswith("test_") for c in changes)
    # Applied changes carry a real diff.
    assert any(c["diff"] and "+" in c["diff"] for c in changes)


def test_tests_actually_run(client, dev_seeded):
    tid = client.post("/api/v1/development/run", json={"title": "Add timestamp util"}).json()[
        "data"
    ]["id"]
    tests = client.get(f"/api/v1/development/tasks/{tid}").json()["data"]["tests"]
    kinds = {t["kind"]: t for t in tests}
    assert kinds["compile"]["status"] == "passed"
    assert kinds["unit"]["status"] == "passed"
    assert kinds["unit"]["passed_count"] >= 2  # real pytest ran the generated tests


def test_review_runs(client, dev_seeded):
    tid = client.post("/api/v1/development/run", json={"title": "Add slug helper"}).json()["data"][
        "id"
    ]
    review = client.get(f"/api/v1/development/tasks/{tid}").json()["data"]["review"]
    assert review["outcome"] in ("approved", "changes_requested")
    assert 0 <= review["score"] <= 100
    dims = {c["dimension"] for c in review["comments"]}
    assert "test_coverage" in dims and "architecture" in dims


def test_pull_request_draft(client, dev_seeded):
    tid = client.post("/api/v1/development/run", json={"title": "Add config loader"}).json()[
        "data"
    ]["id"]
    pr = client.get(f"/api/v1/development/tasks/{tid}").json()["data"]["pull_request"]
    assert pr["status"] == "draft"
    assert pr["title"].startswith("feat:")
    assert pr["commit_count"] >= 1 and pr["files_changed"] == 3
    assert pr["additions"] > 0
    assert "Summary" in pr["body"] and "not pushed or merged" in pr["body"].lower()
    assert pr["release_notes"]


def test_timeline_has_all_stages(client, dev_seeded):
    tid = client.post("/api/v1/development/run", json={"title": "Add greeter"}).json()["data"]["id"]
    timeline = client.get(f"/api/v1/development/tasks/{tid}/timeline").json()["data"]
    stages = {s["stage"] for s in timeline}
    assert {
        "planning",
        "implementation",
        "testing",
        "review",
        "documentation",
        "git",
        "pull_request",
    } <= stages
    assert all(s["status"] == "completed" for s in timeline)


def test_documentation_written_to_knowledge(client, dev_seeded):
    client.post("/api/v1/development/run", json={"title": "Add health checker"})
    docs = client.get("/api/v1/knowledge/documents").json()["data"]
    assert any(d["title"].startswith("Implementation:") for d in docs)


def test_approval_workflow(client, dev_seeded):
    tid = client.post("/api/v1/development/run", json={"title": "Add pinger"}).json()["data"]["id"]
    # Pending approvals lists this task.
    pending = client.get("/api/v1/development/pending-approvals").json()["data"]
    assert any(t["id"] == tid for t in pending)
    # Approve — never merges, just records.
    resp = client.post(
        f"/api/v1/development/tasks/{tid}/approve",
        json={"decision": "approved", "notes": "LGTM"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "approved"
    assert data["pull_request"]["status"] == "approved"


def test_rejection_workflow(client, dev_seeded):
    tid = client.post("/api/v1/development/run", json={"title": "Add risky change"}).json()["data"][
        "id"
    ]
    resp = client.post(
        f"/api/v1/development/tasks/{tid}/approve",
        json={"decision": "rejected", "notes": "not needed"},
    )
    assert resp.json()["data"]["status"] == "rejected"


def test_founder_dashboard(client, dev_seeded):
    client.post("/api/v1/development/run", json={"title": "Add util one"})
    d = client.get("/api/v1/development/founder-dashboard").json()["data"]
    assert d["total_tasks"] >= 1
    assert d["pending_approvals"] >= 1
    assert d["open_pull_requests"] >= 1
    assert len(d["recent_tasks"]) >= 1


def test_ai_dashboard(client, dev_seeded):
    client.post("/api/v1/development/run", json={"title": "Add util two"})
    d = client.get("/api/v1/development/ai-dashboard").json()["data"]
    assert d["current_task"] is not None
    assert d["branch"] and d["timeline"]


def test_metrics_recorded(client, dev_seeded):
    tid = client.post("/api/v1/development/run", json={"title": "Add metrics util"}).json()["data"][
        "id"
    ]
    m = client.get(f"/api/v1/development/tasks/{tid}").json()["data"]["metrics"]
    assert m["generated_files"] == 3
    assert m["commits"] >= 1
    assert m["tests_passed"] >= 2
    assert m["review_score"] > 0
