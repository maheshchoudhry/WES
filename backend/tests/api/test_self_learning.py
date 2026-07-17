"""Phase 7 (WP9) — self-learning: completed work improves future work."""


def test_task_generates_learning_rules(client, quality_seeded):
    client.post("/api/v1/development/run", json={"title": "Add a slug helper utility"})
    rules = client.get("/api/v1/learning/rules").json()["data"]
    assert rules, "a completed task must generate at least one reusable rule"
    # Rules are evidence-based and typed.
    assert all(r["kind"] for r in rules)
    assert any("compile and pass tests" in r["rule"] for r in rules)


def test_rules_reinforce_and_apply_across_tasks(client, quality_seeded):
    # First task creates rules.
    client.post("/api/v1/development/run", json={"title": "Add a cache helper"})
    before = {r["rule"]: r for r in client.get("/api/v1/learning/rules").json()["data"]}

    # Second task: its plan APPLIES learned rules, and recurring rules reinforce.
    t2 = client.post(
        "/api/v1/development/run", json={"title": "Add a cache eviction helper"}
    ).json()["data"]
    detail = client.get(f"/api/v1/development/tasks/{t2['id']}").json()["data"]
    assert "Applied" in (detail["plan"]["summary"] or "")

    after = {r["rule"]: r for r in client.get("/api/v1/learning/rules").json()["data"]}
    # A shared rule (python compile+tests) recurred → occurrences grew (learning
    # accumulates across tasks).
    shared = "python changes must compile and pass tests before a PR"
    assert shared in after
    assert after[shared]["occurrences"] >= 2

    # Learned rules were applied to the second task (aggregate application count).
    assert sum(r["applied_count"] for r in after.values()) >= 1

    summary = client.get("/api/v1/learning/summary").json()["data"]
    assert summary["total_rules"] >= 1
    assert summary["total_applications"] >= 1
    assert summary["by_kind"]
