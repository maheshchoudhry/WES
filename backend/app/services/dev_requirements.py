"""Requirement extraction, requirement-driven codegen, and verification.

Closes the semantic planning gap: an autonomous task is decomposed into concrete,
individually-checkable requirements; the generated code is built to satisfy each
one; and every requirement is verified against the produced code BEFORE a pull
request is allowed. If any requirement is missing, the PR is rejected.

Deterministic (no LLM): requirements are parsed from the task's title/description
(quoted literals, and "display/show current date/time" phrasing) and verified by
looking for their concrete marker in the generated source. When a live provider is
added (WP2), the same Requirement/verify contract is reused unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# One quote-pair matcher covering straight and smart quotes.
_QUOTE_RE = re.compile(r"[\"'“”‘’]([^\"'“”‘’]{1,80})[\"'“”‘’]")
_DATE_RE = re.compile(r"\b(current|today'?s|the)?\s*date\b", re.IGNORECASE)
_TIME_RE = re.compile(r"\b(current|the)?\s*time\b", re.IGNORECASE)
_DISPLAY_RE = re.compile(r"^\s*(?:display|show|render|add|put)\s+(.+?)\s*$", re.IGNORECASE)


@dataclass
class Requirement:
    """A single, verifiable expectation extracted from a task."""

    kind: str  # "text" | "date" | "time"
    description: str  # human-readable requirement
    expected: str  # concrete marker that MUST appear in the generated source

    def satisfied_by(self, source: str) -> bool:
        return self.expected in source

    def as_dict(self, source: str | None = None) -> dict:
        d = {"kind": self.kind, "description": self.description, "expected": self.expected}
        if source is not None:
            d["satisfied"] = self.satisfied_by(source)
        return d


class RequirementExtractor:
    """Parse concrete requirements from a task's title + description."""

    def extract(self, title: str, description: str | None = None) -> list[Requirement]:
        reqs: list[Requirement] = []
        seen: set[str] = set()

        def add(req: Requirement, key: str) -> None:
            if key not in seen:
                reqs.append(req)
                seen.add(key)

        # Scan line-by-line so multi-line specs yield one requirement per line.
        for line in re.split(r"[\n;]+", f"{title}\n{description or ''}"):
            line = line.strip()
            if not line:
                continue
            low = line.lower()

            # 1) Quoted literals -> exact-text requirements (highest confidence).
            quoted = False
            for m in _QUOTE_RE.finditer(line):
                lit = m.group(1).strip()
                if lit:
                    quoted = True
                    add(
                        Requirement("text", f'Display the text "{lit}"', lit),
                        f"text:{lit.lower()}",
                    )

            # 2) Current date / current time.
            if _DATE_RE.search(low):
                add(
                    Requirement("date", "Display the current date", "toLocaleDateString"),
                    "date",
                )
            if _TIME_RE.search(low):
                add(
                    Requirement("time", "Display the current time", "toLocaleTimeString"),
                    "time",
                )

            # 3) Unquoted "display/show X" where X is not date/time -> text.
            if not quoted:
                m = _DISPLAY_RE.match(line)
                if m:
                    phrase = m.group(1).strip(" .")
                    plow = phrase.lower()
                    if phrase and not _DATE_RE.search(plow) and not _TIME_RE.search(plow):
                        # Skip generic UI-noun-only phrases (e.g. "a welcome card").
                        if not re.search(r"\b(card|section|banner|widget|component|page)\b", plow):
                            add(
                                Requirement("text", f'Display the text "{phrase}"', phrase),
                                f"text:{plow}",
                            )
        return reqs


def build_requirements_card(heading: str, requirements: list[Requirement]) -> str:
    """Build a JSX card that concretely satisfies each requirement.

    Text -> a <p> with the literal; date/time -> a live ``new Date()`` expression.
    With no requirements, a generic informational card is produced (unchanged
    behavior for tasks that carry no explicit display requirements).
    """
    rows: list[str] = []
    for r in requirements:
        if r.kind == "text":
            safe = r.expected.replace("<", "").replace(">", "").replace("{", "").replace("}", "")
            rows.append(f'        <p data-testid="wes-req-text">{safe}</p>')
        elif r.kind == "date":
            rows.append(
                '        <p data-testid="wes-current-date">{new Date().toLocaleDateString()}</p>'
            )
        elif r.kind == "time":
            rows.append(
                '        <p data-testid="wes-current-time">{new Date().toLocaleTimeString()}</p>'
            )
    if not rows:
        rows.append("        <p>Added by the WES autonomous development engine.</p>")
    safe_heading = heading.replace("<", "").replace(">", "")
    body = "\n".join(rows)
    return (
        '      <div className="card wes-auto-card" data-testid="wes-auto-card">\n'
        f"        <h2>{safe_heading}</h2>\n"
        f"{body}\n"
        "      </div>\n"
    )


def verify_requirements(source: str, requirements: list[Requirement]) -> list[dict]:
    """Return a per-requirement verification report against the generated source."""
    return [r.as_dict(source) for r in requirements]
