"""Repository Intelligence API + integration tests (Sprint 12).

Scans a real subtree of the WES backend (``app/providers``) and asserts the
engine understands it: files, symbols, dependency graph, search, impact analysis,
architecture, and metrics."""

import os


def _repo(client):
    repos = client.get("/api/v1/repositories").json()["data"]
    return repos[0]


def test_register_and_scan(client):
    resp = client.post(
        "/api/v1/repositories",
        json={"name": "Providers", "root_path": os.path.abspath("app/providers")},
    )
    assert resp.status_code == 200, resp.text
    repo = resp.json()["data"]
    assert repo["slug"] == "providers"

    scan = client.post(f"/api/v1/repositories/{repo['id']}/scan").json()["data"]
    assert scan["status"] == "completed"
    assert scan["file_count"] >= 5
    assert scan["symbol_count"] > 20
    assert scan["repository"]["primary_language"] == "python"


def test_repo_seeded_metrics(client, repo_seeded):
    repo = _repo(client)
    m = repo["metrics"]
    assert m["file_count"] >= 5
    assert m["class_count"] > 0 and m["function_count"] > 0
    assert m["line_count"] > 100
    assert m["languages"].get("python", 0) >= 5
    assert 0 <= m["health_score"] <= 100


def test_files_and_symbols(client, repo_seeded):
    repo = _repo(client)
    files = client.get(f"/api/v1/repositories/{repo['id']}/files").json()["data"]
    assert any(f["name"] == "external.py" for f in files)
    symbols = client.get(f"/api/v1/repositories/{repo['id']}/symbols").json()["data"]
    names = {s["name"] for s in symbols}
    assert "ClaudeProvider" in names or "OpenAIProvider" in names
    # Methods carry a parent + signature.
    execute = next((s for s in symbols if s["name"] == "execute"), None)
    assert execute is not None and execute["symbol_type"] == "method"


def test_symbol_type_filter(client, repo_seeded):
    repo = _repo(client)
    classes = client.get(f"/api/v1/repositories/{repo['id']}/symbols?symbol_type=class").json()[
        "data"
    ]
    assert classes and all(s["symbol_type"] == "class" for s in classes)


def test_search(client, repo_seeded):
    repo = _repo(client)
    hits = client.get(f"/api/v1/repositories/{repo['id']}/search?q=provider").json()["data"]
    assert any("Provider" in h["term"] for h in hits)
    # Filter by kind.
    files = client.get(f"/api/v1/repositories/{repo['id']}/search?q=external&kind=file").json()[
        "data"
    ]
    assert all(h["kind"] == "file" for h in files)


def test_import_graph(client, repo_seeded):
    repo = _repo(client)
    graph = client.get(f"/api/v1/repositories/{repo['id']}/import-graph").json()["data"]
    assert len(graph["nodes"]) > 0 and len(graph["edges"]) > 0
    # external.py imports base + http internally.
    assert any(e["source"] == "external.py" and "base" in e["target"] for e in graph["edges"])


def test_external_dependencies(client, repo_seeded):
    repo = _repo(client)
    deps = client.get(f"/api/v1/repositories/{repo['id']}/dependencies").json()["data"]
    pkgs = {d["package"] for d in deps}
    assert "httpx" in pkgs or "typing" in pkgs


def test_architecture(client, repo_seeded):
    repo = _repo(client)
    layers = client.get(f"/api/v1/repositories/{repo['id']}/architecture").json()["data"]
    assert len(layers) >= 1
    assert sum(a["file_count"] for a in layers) >= 5


def test_impact_analysis(client, repo_seeded):
    repo = _repo(client)
    impact = client.get(f"/api/v1/repositories/{repo['id']}/impact?file_path=external.py").json()[
        "data"
    ]
    assert any("base" in d for d in impact["dependencies"])
    assert "registry.py" in impact["dependents"]
    assert "potential_breakages" in impact and "related_tests" in impact


def test_references_cross_reference(client, repo_seeded):
    repo = _repo(client)
    refs = client.get(f"/api/v1/repositories/{repo['id']}/references?name=ExternalProvider").json()[
        "data"
    ]
    assert "definitions" in refs and "relationships" in refs
    # ClaudeProvider inherits from ExternalProvider (a relationship edge).
    assert any(rel["target"] == "ExternalProvider" for rel in refs["relationships"])


def test_dashboard(client, repo_seeded):
    repo = _repo(client)
    d = client.get(f"/api/v1/repositories/{repo['id']}/dashboard").json()["data"]
    assert d["metrics"]["symbol_count"] > 0
    assert "architecture" in d and "external_dependencies" in d and "issues" in d


def test_ai_context(client, repo_seeded):
    repo = _repo(client)
    ctx = client.get(f"/api/v1/repositories/{repo['id']}/ai-context?keywords=provider").json()[
        "data"
    ]
    assert ctx["repository"] is not None
    assert "architecture" in ctx and "relevant_symbols" in ctx


def test_rescan_is_idempotent(client, repo_seeded):
    repo = _repo(client)
    before = client.get(f"/api/v1/repositories/{repo['id']}").json()["data"]["metrics"][
        "file_count"
    ]
    client.post(f"/api/v1/repositories/{repo['id']}/scan")
    after = client.get(f"/api/v1/repositories/{repo['id']}").json()["data"]["metrics"]["file_count"]
    assert before == after  # no duplication


def test_ai_execution_retrieves_repository_context(client, orch_seeded, repo_seeded):
    """AI execution retrieves repository context before code work."""
    be = client.get("/api/v1/ai-employees?search=Ritchie").json()["data"][0]
    resp = client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "mock"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "completed"
