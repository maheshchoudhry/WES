"""Seed data for the AI Company Core (Sprint 06).

Creates the AI organization: three departments, twelve roles, a capability
catalog, and twelve AI employees with their reporting hierarchy, responsibilities,
capabilities, and KPIs. Idempotent (skips when AI departments already exist).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.ai_enums import AIDecisionAuthority, AIRoleLevel
from app.domain.enums import EntityStatus
from app.models.ai import (
    AIKPI,
    AICapability,
    AIDepartment,
    AIEmployee,
    AIResponsibility,
    AIRole,
)

# code, name, focus
DEPARTMENTS = [
    ("AI-DEPT-01", "Executive", "Company strategy and technical leadership"),
    ("AI-DEPT-02", "Product", "Product direction and what to build"),
    ("AI-DEPT-03", "Engineering", "Designing and building the software"),
]

# code, title, level, is_executive_head
ROLES = [
    ("CEO", "AI CEO", AIRoleLevel.EXECUTIVE, True),
    ("CTO", "AI CTO", AIRoleLevel.EXECUTIVE, False),
    ("CHIEF_ARCHITECT", "Chief Software Architect", AIRoleLevel.EXECUTIVE, False),
    ("PRODUCT_MANAGER", "AI Product Manager", AIRoleLevel.LEAD, False),
    ("BACKEND_ENGINEER", "Backend Engineer AI", AIRoleLevel.OPERATIONAL, False),
    ("FRONTEND_ENGINEER", "Frontend Engineer AI", AIRoleLevel.OPERATIONAL, False),
    ("AI_ENGINEER", "AI Engineer", AIRoleLevel.OPERATIONAL, False),
    ("QA_ENGINEER", "QA Engineer AI", AIRoleLevel.OPERATIONAL, False),
    ("DEVOPS_ENGINEER", "DevOps Engineer AI", AIRoleLevel.OPERATIONAL, False),
    ("SECURITY_ENGINEER", "Security Engineer AI", AIRoleLevel.OPERATIONAL, False),
    ("UIUX_DESIGNER", "UI/UX Designer AI", AIRoleLevel.OPERATIONAL, False),
    ("TECH_WRITER", "Technical Writer AI", AIRoleLevel.OPERATIONAL, False),
]

# code, name
CAPABILITIES = [
    ("strategy", "Strategy"),
    ("technical_leadership", "Technical Leadership"),
    ("architecture", "Architecture"),
    ("product_management", "Product Management"),
    ("backend_development", "Backend Development"),
    ("frontend_development", "Frontend Development"),
    ("ai_ml", "AI / ML"),
    ("testing", "Testing"),
    ("devops", "DevOps"),
    ("security", "Security"),
    ("design", "Design"),
    ("documentation", "Documentation"),
    ("code_review", "Code Review"),
]

# code, name, dept, role, manager, authority, decision_scope,
# capabilities, responsibilities, kpis[(name,target,unit)]
EMPLOYEES = [
    (
        "AI-EMP-001",
        "Ada",
        "AI-DEPT-01",
        "CEO",
        None,
        AIDecisionAuthority.EXECUTIVE,
        "Company-wide strategy and direction",
        ["strategy", "technical_leadership"],
        ["Set company vision and strategy", "Approve major initiatives"],
        [("Roadmap delivery", "90", "%")],
    ),
    (
        "AI-EMP-002",
        "Turing",
        "AI-DEPT-01",
        "CTO",
        "AI-EMP-001",
        AIDecisionAuthority.EXECUTIVE,
        "Technology strategy and the engineering organization",
        ["technical_leadership", "architecture"],
        ["Own technology strategy", "Lead the engineering organization"],
        [("System uptime", "99.9", "%")],
    ),
    (
        "AI-EMP-003",
        "Hopper",
        "AI-DEPT-01",
        "CHIEF_ARCHITECT",
        "AI-EMP-002",
        AIDecisionAuthority.EXECUTIVE,
        "System architecture and engineering standards",
        ["architecture", "code_review"],
        ["Define system architecture", "Uphold engineering standards"],
        [("Architecture review coverage", "100", "%")],
    ),
    (
        "AI-EMP-004",
        "Lovelace",
        "AI-DEPT-02",
        "PRODUCT_MANAGER",
        "AI-EMP-001",
        AIDecisionAuthority.LEAD,
        "Product roadmap and priorities",
        ["product_management"],
        ["Own the product roadmap", "Prioritize the backlog"],
        [("Roadmap delivery", "85", "%")],
    ),
    (
        "AI-EMP-005",
        "Ritchie",
        "AI-DEPT-03",
        "BACKEND_ENGINEER",
        "AI-EMP-003",
        AIDecisionAuthority.OPERATIONAL,
        "Backend services within assigned scope",
        ["backend_development", "code_review"],
        ["Build and maintain backend services", "Write and maintain tests"],
        [("PR throughput", "20", "/sprint")],
    ),
    (
        "AI-EMP-006",
        "Resig",
        "AI-DEPT-03",
        "FRONTEND_ENGINEER",
        "AI-EMP-003",
        AIDecisionAuthority.OPERATIONAL,
        "Frontend within assigned scope",
        ["frontend_development"],
        ["Build UI components", "Ensure accessibility"],
        [("UI defects", "<5", "/release")],
    ),
    (
        "AI-EMP-007",
        "Hinton",
        "AI-DEPT-03",
        "AI_ENGINEER",
        "AI-EMP-003",
        AIDecisionAuthority.OPERATIONAL,
        "AI/ML features within assigned scope",
        ["ai_ml"],
        ["Develop AI capabilities", "Evaluate and tune models"],
        [("Model accuracy", "90", "%")],
    ),
    (
        "AI-EMP-008",
        "Dijkstra",
        "AI-DEPT-03",
        "QA_ENGINEER",
        "AI-EMP-003",
        AIDecisionAuthority.OPERATIONAL,
        "Quality assurance",
        ["testing"],
        ["Design test plans", "Verify releases"],
        [("Test coverage", "85", "%")],
    ),
    (
        "AI-EMP-009",
        "Hamilton",
        "AI-DEPT-03",
        "DEVOPS_ENGINEER",
        "AI-EMP-003",
        AIDecisionAuthority.OPERATIONAL,
        "CI/CD and infrastructure",
        ["devops"],
        ["Maintain CI/CD pipelines", "Manage environments"],
        [("Deploy frequency", "daily", "")],
    ),
    (
        "AI-EMP-010",
        "Diffie",
        "AI-DEPT-03",
        "SECURITY_ENGINEER",
        "AI-EMP-003",
        AIDecisionAuthority.OPERATIONAL,
        "Security posture within assigned scope",
        ["security"],
        ["Review changes for security", "Run security scans"],
        [("Critical vulnerabilities", "0", "")],
    ),
    (
        "AI-EMP-011",
        "Norman",
        "AI-DEPT-03",
        "UIUX_DESIGNER",
        "AI-EMP-004",
        AIDecisionAuthority.OPERATIONAL,
        "Design within product scope",
        ["design"],
        ["Design user flows", "Maintain the design system"],
        [("Usability score", "4.5", "/5")],
    ),
    (
        "AI-EMP-012",
        "Strunk",
        "AI-DEPT-03",
        "TECH_WRITER",
        "AI-EMP-004",
        AIDecisionAuthority.OPERATIONAL,
        "Documentation",
        ["documentation"],
        ["Write and maintain documentation", "Keep guides current"],
        [("Docs coverage", "90", "%")],
    ),
]


def seed_ai(db: Session) -> bool:
    """Seed the AI organization. Returns True if seeded, False if already present."""
    if db.query(AIDepartment).count() > 0:
        return False

    departments = {}
    for code, name, focus in DEPARTMENTS:
        d = AIDepartment(code=code, name=name, focus=focus, status=EntityStatus.ACTIVE)
        db.add(d)
        departments[code] = d

    roles = {}
    for code, title, level, is_head in ROLES:
        r = AIRole(code=code, title=title, level=level, is_executive_head=is_head)
        db.add(r)
        roles[code] = r

    capabilities = {}
    for code, name in CAPABILITIES:
        c = AICapability(code=code, name=name)
        db.add(c)
        capabilities[code] = c

    db.flush()

    employees: dict[str, AIEmployee] = {}
    for (
        code,
        name,
        dept_code,
        role_code,
        manager_code,
        authority,
        scope,
        cap_codes,
        responsibilities,
        kpis,
    ) in EMPLOYEES:
        emp = AIEmployee(
            employee_code=code,
            name=name,
            department_id=departments[dept_code].id,
            role_id=roles[role_code].id,
            manager_id=employees[manager_code].id if manager_code else None,
            authority=authority,
            decision_scope=scope,
            version=1,
        )
        emp.capabilities = [capabilities[c] for c in cap_codes]
        emp.responsibilities = [
            AIResponsibility(description=d, position=i) for i, d in enumerate(responsibilities)
        ]
        emp.kpis = [AIKPI(name=n, target=t, unit=u) for (n, t, u) in kpis]
        db.add(emp)
        db.flush()
        employees[code] = emp

    return True
