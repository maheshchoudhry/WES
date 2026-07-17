# Information Flow

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Active &nbsp;|&nbsp; **Owner:** WES

How work information moves through WES, from requirement to release. Mirrors the SDLC in [Volume 04](../../Blueprint/Volume-04-Engineering-System/README.md).

```
Requirement
   ↓
Planning
   ↓
Architecture
   ↓
Engineering
   ↓
QA
   ↓
Documentation
   ↓
Approval
   ↓
Release
```

| Stage | Owner | Passes To |
|-------|-------|-----------|
| **Requirement** | Product Manager | Project Manager |
| **Planning** | Project Manager | Software Architect |
| **Architecture** | Software Architect | Engineers |
| **Engineering** | Engineers (Frontend / Backend / AI) | QA Engineer |
| **QA** | QA Engineer | Technical Writer |
| **Documentation** | Technical Writer | Studio Director |
| **Approval** | Studio Director (Founder if strategic) | DevOps / Automation Engineer |
| **Release** | DevOps / Automation Engineer | — |

Each handoff carries the context the next stage needs. Security review runs alongside Engineering and QA. Blocked stages follow the [Escalation Flow](./Escalation-Flow.md).

---

_See also: [Approval Flow](./Approval-Flow.md) · [Escalation Flow](./Escalation-Flow.md)_
