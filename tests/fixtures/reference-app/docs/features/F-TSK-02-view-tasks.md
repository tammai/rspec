---
id: F-TSK-02
module: TSK
priority: MVP
depends_on: [F-TSK-01]
status: todo
---
# F-TSK-02: View tasks

## Story
As a member, I want to view tasks so that work is tracked.

## Acceptance criteria
- [ ] **F-TSK-02.AC1** Given a task "Write report" exists, when a member opens it by its id, then the title "Write report" is shown. `[docs]`
- [ ] **F-TSK-02.AC2** Given no task has the id "missing", when a member opens "missing", then 404 is returned. `[docs]`
- [ ] **F-TSK-02.AC3** Given 2 tasks exist, when a member lists tasks, then the count 2 is shown. `[docs]`

## Failure modes
- Unknown id → F-TSK-02.AC2

## Must never break
- none

## Differences from the original
- none

## Sources
- README.md, API
