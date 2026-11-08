---
id: F-TSK-01
module: TSK
priority: MVP
depends_on: []
status: todo
---
# F-TSK-01: Create task

## Story
As a member, I want to create task so that work is tracked.

## Acceptance criteria
- [ ] **F-TSK-01.AC1** Given 2 tasks exist, when a member creates "Write report", then it is shown as TSK-3. `[docs]`
- [ ] **F-TSK-01.AC2** Given a member, when they create a task with an empty title, then 400 is returned. `[inferred]`
- [ ] **F-TSK-01.AC3** Given nobody is signed in, when someone creates "Write report", then 401 is returned. `[docs]`

## Failure modes
- Empty title → F-TSK-01.AC2
- Not signed in → F-TSK-01.AC3

## Must never break
- none

## Differences from the original
- none

## Sources
- README.md, API
