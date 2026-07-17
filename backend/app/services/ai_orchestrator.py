"""Real AI-employee orchestration (WP7, Phase 3).

Turns the development workflow's role *labels* into actual acting employees. For
each stage the orchestrator resolves a REAL ``ai_employees`` row and builds an
:class:`Agent` carrying that employee's responsibilities, decision rules,
authority, context, and **selected provider** (via the existing
``ProviderService.provider_for_employee`` — mock until a live provider is keyed,
which is WP2). It records which employee performed each stage and the **handoffs**
between them.

No LLM is required for this phase: employees act through the existing deterministic
services; what becomes real is *who* acts, *their* policy/authority/provider, and
the recorded collaboration. When a live provider is configured (WP2), each agent's
selected provider performs the reasoning without changing this contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.ai_enums import AIDecisionAuthority
from app.models.ai import AIEmployee, AIResponsibility, AIRole

# Role keyword -> decision rules the employee applies at their stage.
_DECISION_RULES: dict[str, list[str]] = {
    "ceo": [
        "Approve only work aligned with the stated business objective.",
        "Delegate execution to the responsible employees.",
    ],
    "product": [
        "Every task must have acceptance criteria.",
        "Reject scope with no concrete deliverable.",
    ],
    "architect": [
        "Reuse the existing layered architecture; no schema/API rewrites without cause.",
        "Assess impact on dependents before approving a change.",
    ],
    "backend": [
        "Modify existing files with AST-safe edits; never break compilation.",
        "All code must compile and tests must pass.",
    ],
    "frontend": [
        "Match the existing WES design language.",
        "Keep typecheck clean.",
    ],
    "qa": [
        "Do not pass a task with failing tests.",
        "Verify every requested requirement is present.",
    ],
    "security": [
        "Zero critical findings required to pass the quality gate.",
        "Flag any secret or unsafe pattern.",
    ],
    "writer": [
        "Every change updates the knowledge base.",
        "Document the approach and verification.",
    ],
    "devops": [
        "Never push or merge; production is Founder-gated.",
        "Every deployment must be reversible.",
    ],
}

# Which employee role performs each development stage.
STAGE_ROLE: dict[str, str] = {
    "intent": "product",
    "planning": "product",
    "repo_analysis": "architect",
    "knowledge": "architect",
    "implementation": "backend",
    "testing": "qa",
    "verification": "qa",
    "review": "architect",
    "quality_gate": "security",
    "documentation": "writer",
    "git": "devops",
    "pull_request": "devops",
    "approval": "ceo",
}


@dataclass
class Agent:
    employee: AIEmployee
    role_title: str
    role_keyword: str
    responsibilities: list[str]
    decision_rules: list[str]
    authority: str
    provider_name: str
    context: dict = field(default_factory=dict)

    @property
    def label(self) -> str:
        return f"{self.employee.name} ({self.role_title})"


class AIEmployeeOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self._pairs: list[tuple[str, AIEmployee]] | None = None

    # -- resolution --------------------------------------------------------

    def _employee_pairs(self) -> list[tuple[str, AIEmployee]]:
        if self._pairs is None:
            rows = self.db.execute(
                select(AIRole.title, AIEmployee)
                .join(AIEmployee, AIEmployee.role_id == AIRole.id)
                .where(AIEmployee.is_deleted.is_(False))
            ).all()
            self._pairs = [(t, e) for t, e in rows]
        return self._pairs

    def _find(self, keyword: str) -> tuple[str, AIEmployee] | None:
        if keyword == "ceo":
            emp = self.db.scalar(
                select(AIEmployee)
                .where(
                    AIEmployee.authority == AIDecisionAuthority.EXECUTIVE,
                    AIEmployee.manager_id.is_(None),
                    AIEmployee.is_deleted.is_(False),
                )
                .limit(1)
            )
            if emp is not None:
                role = self.db.get(AIRole, emp.role_id)
                return (role.title if role else "AI CEO", emp)
        for title, emp in self._employee_pairs():
            if keyword in title.lower():
                return (title, emp)
        return None

    def _provider_name(self, employee: AIEmployee) -> str:
        try:
            from app.services.providers_service import ProviderService

            return ProviderService(self.db).provider_for_employee(employee).name
        except Exception:
            return "mock"

    def agent_for(self, role_keyword: str) -> Agent | None:
        found = self._find(role_keyword)
        if found is None:
            return None
        title, emp = found
        responsibilities = [
            r.description
            for r in self.db.scalars(
                select(AIResponsibility).where(AIResponsibility.ai_employee_id == emp.id)
            ).all()
        ]
        authority = emp.authority.value if hasattr(emp.authority, "value") else emp.authority
        return Agent(
            employee=emp,
            role_title=title,
            role_keyword=role_keyword,
            responsibilities=responsibilities,
            decision_rules=_DECISION_RULES.get(role_keyword, []),
            authority=authority,
            provider_name=self._provider_name(emp),
        )

    def agent_for_stage(self, stage: str) -> Agent | None:
        return self.agent_for(STAGE_ROLE.get(stage, "backend"))

    def team(self) -> list[Agent]:
        """The standard engineering team as acting agents (deduped by employee)."""
        seen: set = set()
        out: list[Agent] = []
        for kw in ["ceo", "product", "architect", "backend", "frontend", "qa", "security", "writer", "devops"]:
            a = self.agent_for(kw)
            if a and a.employee.id not in seen:
                seen.add(a.employee.id)
                out.append(a)
        return out

    @staticmethod
    def serialize_agent(a: Agent) -> dict:
        return {
            "employee": a.employee.name,
            "employee_code": a.employee.employee_code,
            "role": a.role_title,
            "authority": a.authority,
            "provider": a.provider_name,
            "responsibilities": a.responsibilities,
            "decision_rules": a.decision_rules,
        }
