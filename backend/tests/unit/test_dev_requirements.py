"""Requirement extraction, requirement-driven codegen, and verification."""

from app.services.dev_requirements import (
    RequirementExtractor,
    build_requirements_card,
    verify_requirements,
)


def test_extracts_quoted_text_date_and_time():
    reqs = RequirementExtractor().extract(
        "Update the Founder Dashboard",
        'Display "Hello Choudhary"\nDisplay current date\nDisplay current time',
    )
    kinds = [r.kind for r in reqs]
    assert kinds.count("text") == 1
    assert "date" in kinds and "time" in kinds
    text = next(r for r in reqs if r.kind == "text")
    assert text.expected == "Hello Choudhary"


def test_card_satisfies_all_requirements():
    reqs = RequirementExtractor().extract(
        "x", 'Display "Hello Choudhary"\nDisplay current date\nDisplay current time'
    )
    card = build_requirements_card("Greeting", reqs)
    report = verify_requirements(card, reqs)
    assert all(r["satisfied"] for r in report)
    assert "Hello Choudhary" in card
    assert "toLocaleDateString" in card and "toLocaleTimeString" in card


def test_verification_detects_missing_requirement():
    reqs = RequirementExtractor().extract(
        "x", 'Display "Hello Choudhary"\nDisplay current date\nDisplay current time'
    )
    # A card that forgot the time requirement.
    broken = (
        '<div className="card">\n'
        "  <p>Hello Choudhary</p>\n"
        "  <p>{new Date().toLocaleDateString()}</p>\n"
        "</div>"
    )
    report = verify_requirements(broken, reqs)
    missing = [r for r in report if not r["satisfied"]]
    assert len(missing) == 1
    assert missing[0]["kind"] == "time"


def test_no_requirements_yields_generic_card():
    reqs = RequirementExtractor().extract("Add a Welcome Card to the Founder Dashboard")
    assert reqs == []  # "card"/UI-noun only -> no concrete display requirement
    card = build_requirements_card("Welcome Card", reqs)
    assert "autonomous development engine" in card
