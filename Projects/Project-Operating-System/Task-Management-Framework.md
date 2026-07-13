# Task Management Framework

**Version:** v1.0 &nbsp;|&nbsp; **Status:** Active &nbsp;|&nbsp; **Owner:** WES

A generic framework for managing tasks within any WES project.

## Task Creation

Tasks are created from planned work. Each task has a clear title, description, acceptance criteria, and a linked issue. Tasks should be small enough to complete in one focused effort (see the [Definition of Ready](../../Blueprint/Volume-04-Engineering-System/README.md)).

## Task Assignment

Each task is assigned to exactly one owner within their scope and capacity ([Employee Operating System](../../Company/Employee-Operating-System/README.md)). The owner is accountable from assignment to completion.

## Priority Levels

| Level | Meaning |
|-------|---------|
| **P0 — Critical** | Blocks the project; address immediately. |
| **P1 — High** | Important; needed for the current milestone. |
| **P2 — Medium** | Standard priority. |
| **P3 — Low** | Nice to have; deferrable. |

## Task Status

Uses the standard [Employee States](../../Company/Employee-Operating-System/Employee-States.md): `Available → Assigned → Working → Waiting for Review → Completed`, with `Blocked` when stalled.

## Dependencies

Dependencies between tasks are recorded explicitly. A task blocked by a dependency is marked **Blocked** and escalated if it cannot proceed.

## Completion Rules

A task is complete only when it meets its acceptance criteria and the [Definition of Done](../../Blueprint/Volume-04-Engineering-System/README.md): built, tested, reviewed, documented, and merged.

---

_See also: [Sprint Framework](./Sprint-Framework.md) · [Project Lifecycle](./Project-Lifecycle.md)_
