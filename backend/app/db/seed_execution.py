"""Seed data for the AI Execution Engine (Sprint 08).

Creates workspaces for every AI employee, a prompt library, an SOP library,
decision rules per role, an execution queue with history, a review queue, and a
persisted handoff workflow chain. Idempotent (skips when workspaces exist).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.domain.execution_enums import (
    DecisionRuleType,
    ExecutionStatus,
    HandoffStatus,
    PromptType,
    ReviewStatus,
    SOPCategory,
)
from app.domain.work_enums import Priority
from app.models.ai import AIEmployee, AIRole
from app.models.execution import (
    SOP,
    AIWorkspace,
    DecisionRule,
    ExecutionContext,
    ExecutionHistory,
    ExecutionQueueItem,
    Handoff,
    PromptTemplate,
    ReviewItem,
)
from app.models.work import WorkItem

PROMPTS = [
    (
        "PROMPT-SYS",
        "System Prompt",
        PromptType.SYSTEM,
        "You are an AI employee of WES OS. Operate within your role, follow SOPs, and respect decision rules.",
    ),
    (
        "PROMPT-ROLE",
        "Role Prompt",
        PromptType.ROLE,
        "Act according to your role's responsibilities and authority.",
    ),
    (
        "PROMPT-TASK",
        "Task Prompt",
        PromptType.TASK,
        "Complete the assigned task, meeting its acceptance criteria.",
    ),
    (
        "PROMPT-REVIEW",
        "Review Prompt",
        PromptType.REVIEW,
        "Review the submitted work against standards and the Definition of Done.",
    ),
    (
        "PROMPT-ESC",
        "Escalation Prompt",
        PromptType.ESCALATION,
        "Escalate to your manager when a decision exceeds your authority.",
    ),
]

SOPS = [
    (
        "SOP-CODE",
        "Coding SOP",
        SOPCategory.CODING,
        "Write small, tested, reviewed changes. Follow the style guide.",
    ),
    (
        "SOP-REVIEW",
        "Review SOP",
        SOPCategory.REVIEW,
        "Check correctness, standards, tests, and clarity before approving.",
    ),
    (
        "SOP-TEST",
        "Testing SOP",
        SOPCategory.TESTING,
        "Cover new behavior with unit and integration tests.",
    ),
    (
        "SOP-DEPLOY",
        "Deployment SOP",
        SOPCategory.DEPLOYMENT,
        "Deploy from a green main after checks pass.",
    ),
    (
        "SOP-DOCS",
        "Documentation SOP",
        SOPCategory.DOCUMENTATION,
        "Document decisions and keep guides current.",
    ),
    (
        "SOP-SEC",
        "Security SOP",
        SOPCategory.SECURITY,
        "No secrets in code; review changes for security.",
    ),
]

# Founder -> CEO -> PM -> Architect -> Backend -> Frontend -> QA -> Writer -> Founder Review
WORKFLOW = [
    (None, "AI-EMP-001", "Founder -> AI CEO", HandoffStatus.COMPLETED),
    ("AI-EMP-001", "AI-EMP-004", "AI CEO -> Product Manager", HandoffStatus.COMPLETED),
    ("AI-EMP-004", "AI-EMP-003", "Product Manager -> Chief Architect", HandoffStatus.COMPLETED),
    ("AI-EMP-003", "AI-EMP-005", "Chief Architect -> Backend Engineer", HandoffStatus.COMPLETED),
    ("AI-EMP-005", "AI-EMP-006", "Backend -> Frontend Engineer", HandoffStatus.ACCEPTED),
    ("AI-EMP-006", "AI-EMP-008", "Frontend -> QA Engineer", HandoffStatus.PENDING),
    ("AI-EMP-008", "AI-EMP-012", "QA -> Technical Writer", HandoffStatus.PENDING),
    ("AI-EMP-012", "AI-EMP-001", "Technical Writer -> Founder Review", HandoffStatus.PENDING),
]


def _now():
    return datetime.now(timezone.utc)


def seed_execution(db: Session) -> bool:
    """Seed the execution engine. Returns True if seeded, False if already present."""
    if db.query(AIWorkspace).count() > 0:
        return False

    emps = {e.employee_code: e for e in db.query(AIEmployee).all()}
    if not emps:
        return False
    roles = {r.id: r for r in db.query(AIRole).all()}
    tasks = {t.task_code: t for t in db.query(WorkItem).all()}

    # Workspaces for every AI employee.
    for e in emps.values():
        db.add(
            AIWorkspace(
                ai_employee_id=e.id,
                status="active",
                context=f"Workspace for {e.name}. Follow role SOPs and decision rules.",
            )
        )

    # Prompt + SOP libraries.
    prompt_by_code = {}
    for code, name, ptype, content in PROMPTS:
        p = PromptTemplate(
            code=code,
            name=name,
            prompt_type=ptype,
            content=content,
            version=1,
            author="Chief Architect",
        )
        db.add(p)
        prompt_by_code[code] = p
    sop_by_code = {}
    for code, title, cat, content in SOPS:
        s = SOP(code=code, title=title, category=cat, content=content, version=1)
        db.add(s)
        sop_by_code[code] = s
    db.flush()

    # Decision rules per role (authority for all; full set for executives/leads).
    for r in roles.values():
        db.add(
            DecisionRule(
                ai_role_id=r.id,
                rule_type=DecisionRuleType.AUTHORITY_LIMIT,
                name=f"{r.title} authority",
                description=f"Authority limits for {r.title}.",
                authority_limit=r.level.value if hasattr(r.level, "value") else str(r.level),
            )
        )
        lvl = r.level.value if hasattr(r.level, "value") else str(r.level)
        if lvl in ("executive", "lead"):
            db.add(
                DecisionRule(
                    ai_role_id=r.id,
                    rule_type=DecisionRuleType.APPROVAL,
                    name=f"{r.title} approvals",
                    description="May approve work within scope.",
                )
            )
            db.add(
                DecisionRule(
                    ai_role_id=r.id,
                    rule_type=DecisionRuleType.REVIEW,
                    name=f"{r.title} reviews",
                    description="Reviews technical/product work.",
                )
            )
            db.add(
                DecisionRule(
                    ai_role_id=r.id,
                    rule_type=DecisionRuleType.ESCALATION,
                    name=f"{r.title} escalation",
                    description="Escalates beyond-authority decisions.",
                )
            )

    # Execution queue + history for engineers.
    queue_specs = [
        (
            "AI-EMP-005",
            "Implement dashboard API endpoint",
            ExecutionStatus.COMPLETED,
            "WORLD-004",
            "SOP-CODE",
            "PROMPT-TASK",
        ),
        (
            "AI-EMP-006",
            "Build dashboard UI component",
            ExecutionStatus.IN_PROGRESS,
            "WORLD-004",
            "SOP-CODE",
            "PROMPT-TASK",
        ),
        (
            "AI-EMP-007",
            "Integrate AI model interface",
            ExecutionStatus.QUEUED,
            "WORLD-005",
            "SOP-CODE",
            "PROMPT-TASK",
        ),
        (
            "AI-EMP-008",
            "Write API tests",
            ExecutionStatus.QUEUED,
            "WORLD-006",
            "SOP-TEST",
            "PROMPT-TASK",
        ),
        (
            "AI-EMP-009",
            "Configure CI pipeline",
            ExecutionStatus.QUEUED,
            "WORLD-007",
            "SOP-DEPLOY",
            "PROMPT-TASK",
        ),
    ]
    for i, (code, title, st, task_code, sop_code, prompt_code) in enumerate(queue_specs):
        emp = emps.get(code)
        task = tasks.get(task_code)
        started = _now() - timedelta(hours=2) if st != ExecutionStatus.QUEUED else None
        completed = _now() - timedelta(hours=1) if st == ExecutionStatus.COMPLETED else None
        item = ExecutionQueueItem(
            ai_employee_id=emp.id,
            work_item_id=task.id if task else None,
            title=title,
            description=f"{title} per SOP {sop_code}.",
            priority=Priority.HIGH,
            status=st,
            position=i,
            sop_id=sop_by_code[sop_code].id,
            prompt_id=prompt_by_code[prompt_code].id,
            started_at=started,
            completed_at=completed,
        )
        db.add(item)
        db.flush()
        if st == ExecutionStatus.COMPLETED:
            db.add(
                ExecutionHistory(
                    ai_employee_id=emp.id,
                    work_item_id=task.id if task else None,
                    execution_queue_id=item.id,
                    action="queue.completed",
                    output="Endpoint implemented and unit-tested.",
                    status=ExecutionStatus.COMPLETED,
                    duration_seconds=3600,
                )
            )

    # Review queue: Chief Architect reviews Backend's completed work.
    db.add(
        ReviewItem(
            work_item_id=tasks["WORLD-003"].id if "WORLD-003" in tasks else None,
            reviewer_ai_employee_id=emps["AI-EMP-003"].id,
            submitter_ai_employee_id=emps["AI-EMP-005"].id,
            status=ReviewStatus.PENDING,
            notes="Please review the authentication implementation.",
        )
    )

    # Handoff workflow chain for WORLD-004.
    task = tasks.get("WORLD-004")
    for seq, (frm, to, stage, st) in enumerate(WORKFLOW, start=1):
        db.add(
            Handoff(
                work_item_id=task.id if task else None,
                from_ai_employee_id=emps[frm].id if frm else None,
                to_ai_employee_id=emps[to].id,
                stage=stage,
                status=st,
                sequence=seq,
            )
        )

    # Execution context for the Backend engineer.
    be = emps["AI-EMP-005"]
    db.add(
        ExecutionContext(
            ai_employee_id=be.id,
            work_item_id=tasks.get("WORLD-004").id if "WORLD-004" in tasks else None,
            key="repository",
            value="github.com/wes/world",
        )
    )
    db.add(
        ExecutionContext(ai_employee_id=be.id, key="stack", value="FastAPI, SQLAlchemy, PostgreSQL")
    )

    return True
