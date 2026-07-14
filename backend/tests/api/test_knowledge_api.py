"""API + service tests for the Organizational Knowledge Engine (Sprint 10)."""


def _first_doc(client, code="KB-0002"):
    docs = client.get("/api/v1/knowledge/documents").json()["data"]
    return next(d for d in docs if d["code"] == code)


def test_categories_seeded(client, knowledge_seeded):
    cats = client.get("/api/v1/knowledge/categories").json()["data"]
    names = {c["name"] for c in cats}
    assert {"Company", "Engineering", "Security", "Architecture"} <= names
    assert len(cats) == 12
    # Category document counts are computed.
    assert any(c["document_count"] and c["document_count"] > 0 for c in cats)


def test_documents_seeded_with_types(client, knowledge_seeded):
    docs = client.get("/api/v1/knowledge/documents").json()["data"]
    assert len(docs) >= 8
    types = {d["doc_type"] for d in docs}
    assert {"coding_standard", "security_standard", "architecture", "sop"} <= types


def test_document_crud(client, knowledge_seeded):
    # Create.
    resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "title": "Testing Strategy",
            "doc_type": "specification",
            "content": "Unit + integration + runtime verification.",
            "summary": "How WES tests.",
            "keywords": "testing pytest vitest",
            "tags": ["testing", "quality"],
        },
    )
    assert resp.status_code == 200, resp.text
    doc = resp.json()["data"]
    assert doc["code"].startswith("KB-")
    assert doc["version"] == 1
    assert set(doc["tags"]) == {"testing", "quality"}

    # Read (increments views + returns relationships/references keys).
    got = client.get(f"/api/v1/knowledge/documents/{doc['id']}").json()["data"]
    assert got["content"].startswith("Unit")
    assert "relationships" in got and "references" in got

    # Update bumps the version and snapshots history.
    upd = client.patch(
        f"/api/v1/knowledge/documents/{doc['id']}",
        json={"content": "Now with contract tests too.", "change_summary": "Add contract tests"},
    )
    assert upd.status_code == 200
    assert upd.json()["data"]["version"] == 2


def test_versioning(client, knowledge_seeded):
    doc = _first_doc(client)
    # Edit twice to build history.
    client.patch(f"/api/v1/knowledge/documents/{doc['id']}", json={"content": "v2 body"})
    client.patch(f"/api/v1/knowledge/documents/{doc['id']}", json={"content": "v3 body"})
    versions = client.get(f"/api/v1/knowledge/documents/{doc['id']}/versions").json()["data"]
    assert len(versions) >= 3
    assert versions[0]["version"] > versions[-1]["version"]  # newest first

    # Restore an older version creates a new current version.
    restored = client.post(f"/api/v1/knowledge/documents/{doc['id']}/versions/1/restore").json()[
        "data"
    ]
    assert restored["version"] >= 4


def test_relationships_and_graph(client, knowledge_seeded):
    a = _first_doc(client, "KB-0001")
    b = _first_doc(client, "KB-0006")
    resp = client.post(
        "/api/v1/knowledge/relationships",
        json={
            "source_document_id": a["id"],
            "target_document_id": b["id"],
            "relationship_type": "references",
        },
    )
    assert resp.status_code == 200
    rel = resp.json()["data"]
    assert rel["source_title"] and rel["target_title"]

    graph = client.get("/api/v1/knowledge/graph").json()["data"]
    assert len(graph["nodes"]) >= 8
    assert len(graph["edges"]) >= 6  # 5 seeded + 1 new

    related = client.get(f"/api/v1/knowledge/documents/{a['id']}/related").json()["data"]
    assert any(d["code"] == "KB-0006" for d in related)


def test_relationship_rejects_self_link(client, knowledge_seeded):
    a = _first_doc(client, "KB-0001")
    resp = client.post(
        "/api/v1/knowledge/relationships",
        json={
            "source_document_id": a["id"],
            "target_document_id": a["id"],
            "relationship_type": "relates_to",
        },
    )
    assert resp.status_code == 422


def test_search(client, knowledge_seeded):
    # Keyword search hits title/content/keywords.
    hits = client.get("/api/v1/knowledge/search?q=security").json()["data"]
    assert any(d["code"] == "KB-0003" for d in hits)
    # Filter by doc_type.
    standards = client.get("/api/v1/knowledge/search?doc_type=coding_standard").json()["data"]
    assert standards and all(d["doc_type"] == "coding_standard" for d in standards)
    # Filter by category.
    cats = client.get("/api/v1/knowledge/categories").json()["data"]
    sec = next(c for c in cats if c["name"] == "Security")
    by_cat = client.get(f"/api/v1/knowledge/search?category_id={sec['id']}").json()["data"]
    assert all(d["category_name"] == "Security" for d in by_cat)


def test_ai_retrieval_bundle(client, knowledge_seeded):
    bundle = client.get("/api/v1/knowledge/retrieve?keywords=architecture").json()["data"]
    # Every slot the AI must consume before execution is present.
    for slot in (
        "relevant_documents",
        "relevant_sop",
        "relevant_adr",
        "relevant_standards",
        "relevant_decisions",
        "relevant_templates",
        "relevant_references",
    ):
        assert slot in bundle
    assert any(d["doc_type"] == "coding_standard" for d in bundle["relevant_standards"])


def test_approval_workflow(client, knowledge_seeded):
    # Create -> submit -> approve.
    doc = client.post(
        "/api/v1/knowledge/documents",
        json={"title": "Deployment Guide", "doc_type": "deployment_guide", "content": "Steps."},
    ).json()["data"]
    client.post(f"/api/v1/knowledge/documents/{doc['id']}/submit")
    pending = client.get("/api/v1/knowledge/reviews/pending").json()["data"]
    assert any(d["id"] == doc["id"] for d in pending)

    resp = client.post(
        f"/api/v1/knowledge/documents/{doc['id']}/review",
        json={"decision": "approved", "comment": "LGTM"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["decision"] == "approved"

    got = client.get(f"/api/v1/knowledge/documents/{doc['id']}").json()["data"]
    assert got["status"] == "approved"


def test_bookmarks(client, knowledge_seeded):
    doc = _first_doc(client)
    client.post("/api/v1/knowledge/bookmarks", json={"document_id": doc["id"], "note": "ref"})
    marks = client.get("/api/v1/knowledge/bookmarks").json()["data"]
    assert any(b["document_id"] == doc["id"] for b in marks)
    client.request("DELETE", f"/api/v1/knowledge/bookmarks/{doc['id']}")
    marks = client.get("/api/v1/knowledge/bookmarks").json()["data"]
    assert not any(b["document_id"] == doc["id"] for b in marks)


def test_collections(client, knowledge_seeded):
    cols = client.get("/api/v1/knowledge/collections").json()["data"]
    assert any(c["slug"] == "engineering-essentials" for c in cols)
    essentials = next(c for c in cols if c["slug"] == "engineering-essentials")
    detail = client.get(f"/api/v1/knowledge/collections/{essentials['id']}").json()["data"]
    assert detail["document_count"] == 4
    assert len(detail["documents"]) == 4

    # Create a new collection and add a document.
    new = client.post(
        "/api/v1/knowledge/collections", json={"name": "Onboarding", "description": "Start here"}
    ).json()["data"]
    doc = _first_doc(client, "KB-0001")
    updated = client.post(
        f"/api/v1/knowledge/collections/{new['id']}/documents", json={"document_id": doc["id"]}
    ).json()["data"]
    assert updated["document_count"] == 1


def test_adrs(client, knowledge_seeded):
    adrs = client.get("/api/v1/knowledge/adrs").json()["data"]
    assert {a["code"] for a in adrs} >= {"ADR-0001", "ADR-0002"}
    assert all(a["status"] == "accepted" for a in adrs)

    created = client.post(
        "/api/v1/knowledge/adrs",
        json={"title": "Use SQLite for tests", "context": "Fast", "decision": "Adopt"},
    )
    assert created.status_code == 200
    adr = created.json()["data"]
    assert adr["code"].startswith("ADR-")
    resp = client.patch(f"/api/v1/knowledge/adrs/{adr['id']}/status", json={"status": "accepted"})
    assert resp.json()["data"]["status"] == "accepted"


def test_founder_dashboard(client, knowledge_seeded):
    d = client.get("/api/v1/knowledge/founder-dashboard").json()["data"]
    assert d["documents"] >= 8
    assert d["categories"] == 12
    assert d["approved_documents"] >= 4
    assert d["pending_reviews"] >= 1
    assert d["knowledge_health"] in {"healthy", "attention", "empty"}
    assert len(d["recent_knowledge"]) > 0
    assert len(d["most_used"]) > 0


def test_ai_dashboard(client, knowledge_seeded):
    d = client.get("/api/v1/knowledge/ai-dashboard?keywords=architecture").json()["data"]
    for key in (
        "suggested_knowledge",
        "recent_knowledge",
        "architecture_references",
        "coding_standards",
        "sop_recommendations",
    ):
        assert key in d


def test_references_link_to_project(client, knowledge_seeded):
    doc = _first_doc(client, "KB-0008")
    got = client.get(f"/api/v1/knowledge/documents/{doc['id']}").json()["data"]
    assert any(r["entity_type"] == "project" for r in got["references"])


def test_execution_retrieves_knowledge(client, knowledge_seeded):
    """AI execution must retrieve knowledge before running (access log records it)."""
    be = client.get("/api/v1/ai-employees?search=Ritchie").json()["data"][0]
    resp = client.post(
        "/api/v1/orchestration/run", json={"ai_employee_id": be["id"], "provider_name": "mock"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "completed"
    # The retrieval bumped the retrieval counter in analytics.
    stats = client.get("/api/v1/knowledge/analytics").json()["data"]
    assert stats["retrievals"] >= 1
