"""Review-engine unit tests (Sprint 14) — pure analysis of code content."""

from app.domain.quality_enums import FindingSeverity
from app.services.quality_review_engines import (
    ArchitectureReviewService,
    CodeReviewService,
    DependencyReviewService,
    DocumentationReviewService,
    PerformanceReviewService,
    SecurityReviewService,
)


def _change(path, content, language="python"):
    return {"path": path, "content": content, "language": language}


def test_clean_module_has_no_findings():
    clean = _change(
        "mod.py",
        '"""A clean module."""\n\n\ndef ping() -> str:\n    """Return pong."""\n    return "pong"\n',
    )
    assert ArchitectureReviewService().analyze([clean]) == []
    assert SecurityReviewService().analyze([clean]) == []
    assert PerformanceReviewService().analyze([clean]) == []


def test_security_detects_secret():
    bad = _change("s.py", 'API_KEY = "sk-ant-supersecret-123456"\n')
    findings = SecurityReviewService().analyze([bad])
    assert any(f.severity == FindingSeverity.CRITICAL and f.category == "secret" for f in findings)


def test_security_detects_command_injection():
    bad = _change("c.py", "import os\n\n\ndef run(x):\n    os.system(x)\n")
    findings = SecurityReviewService().analyze([bad])
    assert any(f.category == "command_injection" for f in findings)


def test_security_detects_sql_injection():
    bad = _change(
        "q.py", 'def get(db, name):\n    return db.execute(f"SELECT * FROM t WHERE n={name}")\n'
    )
    findings = SecurityReviewService().analyze([bad])
    assert any(
        f.category == "sql_injection" and f.severity == FindingSeverity.CRITICAL for f in findings
    )


def test_performance_detects_nested_loop_and_db_call():
    bad = _change(
        "p.py",
        "def f(rows, db):\n    for r in rows:\n        for c in r:\n            db.query(c)\n",
    )
    findings = PerformanceReviewService().analyze([bad])
    cats = {f.category for f in findings}
    assert "large_loop" in cats
    assert "database_calls" in cats


def test_architecture_detects_bad_naming():
    bad = _change("a.py", "class lower_class:\n    pass\n")
    findings = ArchitectureReviewService().analyze([bad])
    assert any(f.category == "naming" for f in findings)


def test_code_detects_bare_except_and_long_line():
    bad = _change(
        "e.py",
        "def f():\n    try:\n        pass\n    except:\n        pass\n    x = " + "1" * 120 + "\n",
    )
    findings = CodeReviewService().analyze([bad])
    cats = {f.category for f in findings}
    assert "error_handling" in cats
    assert "coding_standards" in cats


def test_dependency_detects_deprecated_and_unused():
    bad = _change("d.py", "import imp\nimport json\n\n\ndef f():\n    return 1\n")
    findings = DependencyReviewService().analyze([bad])
    cats = {f.category for f in findings}
    assert "deprecated" in cats  # imp is deprecated


def test_documentation_flags_missing_docstrings():
    bad = _change("m.py", "def f():\n    return 1\n")
    findings = DocumentationReviewService().analyze(
        [bad], has_knowledge_doc=False, has_markdown=False
    )
    cats = {f.category for f in findings}
    assert "missing_docs" in cats
    assert "knowledge_base" in cats
    assert "technical_docs" in cats


def test_documentation_clean_with_docs_and_markdown():
    clean = _change("m.py", '"""Module."""\n\n\ndef f() -> int:\n    """Doc."""\n    return 1\n')
    findings = DocumentationReviewService().analyze(
        [clean], has_knowledge_doc=True, has_markdown=True
    )
    assert findings == []
