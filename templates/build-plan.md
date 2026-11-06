# Build plan

Every feature in scope, in dependency order, grouped into releases and vertical slices. Release 1 is the MVP; Later features follow in releases 2 and up. Each slice is shippable and testable on its own. Slices are numbered on across releases. Status lives in each story's frontmatter.

## Release 1: MVP
<one line: what a user can do after this release; no feature IDs in release headings or lines>

## Slice 1: <name>
Goal: <what works end to end after this slice>

| Order | Feature | Story | Operations | Schemas | NFRs |
|---|---|---|---|---|---|
| 1 | F-<CODE>-<NN> <name> | features/<file> | <operationId> | <entity> | <NFR-NN> |

Done when: every acceptance criterion of these stories has a passing test.
