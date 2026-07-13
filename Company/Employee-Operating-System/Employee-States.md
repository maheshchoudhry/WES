# Employee States

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Active &nbsp;|&nbsp; **Owner:** WES

Standard operational states that describe what an employee is doing at any moment. The framework is generic and applies to every role.

| State | Meaning |
|-------|---------|
| **Available** | Active and ready to be assigned work. |
| **Assigned** | Has an assignment but has not yet started. |
| **Working** | Actively performing assigned work. |
| **Waiting for Review** | Work submitted; awaiting review or approval. |
| **Blocked** | Cannot proceed due to a dependency or unresolved issue. |
| **Completed** | Assigned work is finished and accepted. |
| **Inactive** | Temporarily suspended or not in service. |

## State Flow (typical)

```
Available → Assigned → Working → Waiting for Review → Completed → Available
                          ↓
                       Blocked → (resolved) → Working
```

An employee's current state is recorded as **Operational State** in its profile and in the [Workforce Register](../Workforce-Register.md).

---

_See also: [Employee Lifecycle](./Employee-Lifecycle.md) · [Operational Rules](./Operational-Rules.md)_
