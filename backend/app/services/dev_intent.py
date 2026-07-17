"""Task intent resolution (WP1 integration fix).

The Autonomous Development page sends only a task *title* — no hand-authored
modification spec. Before this resolver, ``run_workflow`` silently fell back to
scaffold generation for every such task, so "Add a Welcome Card to the Founder
Dashboard" produced ``hello_..._dashboard.py`` scaffolds instead of modifying the
real dashboard.

This resolver infers, deterministically and with a full decision log, whether a
task is:

* **modify**       — it references an existing UI page/file we can locate; build a
  modification spec (MODIFY) targeting that real file;
* **modify_unresolved** — it clearly references existing code, but we could not
  resolve a concrete target/anchor. The workflow MUST FAIL here — it must NEVER
  silently scaffold an existing-file intent;
* **new_module**   — no existing file is referenced; scaffolding a new module is
  the correct, explicitly-logged choice.

No LLM is used: matching is over the real repository (``frontend/src/pages``),
by filename and on-page ``<h1>`` text. When a live provider is configured (WP2),
this same decision can be delegated without changing the workflow.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

log = logging.getLogger("wes.dev.intent")

# Words that signal the task is about EXISTING code (a page/screen/file/edit),
# not a brand-new module. If any is present we must resolve a real target or fail.
_MODIFY_SIGNALS = {
    "dashboard",
    "page",
    "component",
    "screen",
    "view",
    "modify",
    "update",
    "edit",
    "change",
    "refactor",
    "rename",
    "delete",
    "remove",
}
_STOPWORDS = {
    "add", "a", "an", "the", "to", "on", "in", "for", "of", "new", "create",
    "please", "with", "and", "make", "show", "display", "hello", "onto", "into",
}
# Fuzzy aliases so "funders/funder/founders dashboard" resolves to the Founder one.
_ALIASES = {"funders": "founder", "funder": "founder", "founders": "founder"}

_ANCHOR_RE = re.compile(r"\{![\w.]+ \? \(")
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL)
_CAMEL_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")


@dataclass
class ResolvedIntent:
    kind: str  # "modify" | "modify_unresolved" | "new_module"
    reason: str
    spec: dict | None = None
    target_file: str | None = None
    decisions: list[str] = field(default_factory=list)
    requirements: list[dict] = field(default_factory=list)


@dataclass
class _Page:
    rel_path: str
    keywords: set[str]
    h1_tokens: set[str]
    anchor: str


def _tokens(text: str) -> set[str]:
    raw = set(re.findall(r"[a-z0-9]+", text.lower())) - _STOPWORDS
    return {_ALIASES.get(t, t) for t in raw}


class TaskIntentResolver:
    def __init__(self, project_root: str):
        self.root = project_root
        self.pages_dir = os.path.join(project_root, "frontend", "src", "pages")

    # -- page discovery ----------------------------------------------------

    def _index_pages(self) -> list[_Page]:
        pages: list[_Page] = []
        if not os.path.isdir(self.pages_dir):
            return pages
        for dirpath, _dirs, files in os.walk(self.pages_dir):
            for fn in files:
                if not fn.endswith(".tsx") or fn.endswith(".test.tsx"):
                    continue
                abs_path = os.path.join(dirpath, fn)
                try:
                    with open(abs_path, encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                except OSError:
                    continue
                anchor_m = _ANCHOR_RE.search(content)
                if not anchor_m:
                    continue  # no supported insertion anchor -> not a candidate
                stem = fn[:-4]
                name_tokens = {t.lower() for t in _CAMEL_RE.findall(stem)}
                h1_tokens: set[str] = set()
                for h1 in _H1_RE.findall(content):
                    h1_tokens |= _tokens(re.sub(r"<[^>]+>", " ", h1))
                rel = os.path.relpath(abs_path, self.root)
                pages.append(
                    _Page(rel, name_tokens | h1_tokens, h1_tokens, anchor_m.group(0))
                )
        return pages

    def _best_match(self, tokens: set[str], pages: list[_Page]) -> _Page | None:
        best: _Page | None = None
        best_score = 0.0
        for p in pages:
            overlap = tokens & p.keywords
            if not overlap:
                continue
            # h1 matches weigh more; exact filename-stem token match is a strong bonus.
            score = len(overlap) + 0.5 * len(tokens & p.h1_tokens)
            if "dashboard" in tokens and p.rel_path.endswith("pages/Dashboard.tsx"):
                score += 0.25  # canonical Founder Dashboard tie-break
            if score > best_score:
                best_score, best = score, p
        return best if best_score >= 1 else None

    # -- snippet -----------------------------------------------------------

    @staticmethod
    def _heading(title: str) -> str:
        h = re.sub(
            r"\s+(on|to|in|for|onto|into)\s+(the\s+)?.*?"
            r"(dashboard|page|component|screen|view)\s*$",
            "",
            title,
            flags=re.IGNORECASE,
        )
        h = re.sub(r"^\s*(add|create|make|show|display|new|put)\s+(a|an|the)?\s*", "", h, flags=re.IGNORECASE)
        h = h.strip(" .-") or title.strip()
        return h[:80].title()

    def _card_snippet(self, title: str, requirements) -> str:
        from app.services.dev_requirements import build_requirements_card

        heading = self._heading(title).replace("<", "").replace(">", "")
        return build_requirements_card(heading, requirements)

    # -- public ------------------------------------------------------------

    def resolve(self, title: str, description: str | None = None) -> ResolvedIntent:
        decisions: list[str] = []

        def note(step: str, detail: str) -> None:
            line = f"{step}: {detail}"
            decisions.append(line)
            log.info("intent %s", line)

        text = f"{title} {description or ''}"
        tokens = _tokens(text)
        note("tokenize", f"tokens={sorted(tokens)}")

        signal = tokens & _MODIFY_SIGNALS
        has_path = bool(re.search(r"[\w/]+\.(tsx|ts|jsx|js|py)\b", text))
        note("signal", f"existing-code signal words={sorted(signal)} explicit_path={has_path}")

        if not signal and not has_path:
            note("decision", "no existing-file reference -> CREATE new module (scaffold)")
            return ResolvedIntent(
                "new_module", "No existing file/page referenced.", decisions=decisions
            )

        pages = self._index_pages()
        note("discover", f"indexed {len(pages)} candidate page files with a supported anchor")
        match = self._best_match(tokens, pages)
        if match is None:
            note(
                "decision",
                "existing-code intent but NO target could be resolved -> FAIL "
                "(refusing to silently scaffold)",
            )
            return ResolvedIntent(
                "modify_unresolved",
                "Task references existing code but no matching file/anchor was resolved.",
                decisions=decisions,
            )

        note("target", f"resolved target file = {match.rel_path}")
        note("anchor", f"insertion anchor = {match.anchor!r}")

        from app.services.dev_requirements import RequirementExtractor

        requirements = RequirementExtractor().extract(title, description)
        note(
            "requirements",
            f"extracted {len(requirements)}: "
            + (", ".join(r.description for r in requirements) or "none (generic card)"),
        )
        spec = {
            "target_file": match.rel_path,
            "operation": "insert_before_anchor",
            "anchor": match.anchor,
            "snippet": self._card_snippet(title, requirements),
            "source_root": self.root,
        }
        note("decision", f"MODIFY {match.rel_path} via ModificationPlanner (change_type=modify)")
        return ResolvedIntent(
            "modify",
            "Resolved an existing UI page for modification.",
            spec=spec,
            target_file=match.rel_path,
            decisions=decisions,
            requirements=[r.as_dict() for r in requirements],
        )
