# Approval Flow

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Active &nbsp;|&nbsp; **Owner:** WES

The approval hierarchy for decisions in WES. Decisions are approved at the lowest capable level and rise when they exceed authority — consistent with the [AI Decision Hierarchy](../../Blueprint/Volume-05-AI-System/README.md).

```
Employee
   ↓
Team Lead (Reporting Role)
   ↓
Department Head / Studio Director
   ↓
Executive (Founder / Owner)
```

| Level | Approves |
|-------|----------|
| **Employee** | Work within its own defined scope and authority. |
| **Team Lead / Reporting Role** | Work within the team's scope (e.g., architecture, product scope). |
| **Studio Director** | Major operational decisions across departments. |
| **Founder / Owner** | Strategic, irreversible, or high-risk decisions. |

## Rules

- Routine, in-scope work does not require higher approval but remains reviewable.
- Strategic, irreversible, or high-risk actions always require human approval.
- Approvals are recorded alongside the work (pull request, issue, or decision record).

---

_See also: [Information Flow](./Information-Flow.md) · [Escalation Flow](./Escalation-Flow.md)_
