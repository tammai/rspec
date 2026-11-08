# Build plan

Every feature in scope, in dependency order, grouped into releases and vertical slices. Release 1 is the MVP; Later features follow in releases 2 and up. Each slice is shippable and testable on its own. Slices are numbered on across releases. Status lives in each story's frontmatter.

Acceptance bundle: `<spec>/acceptance/` (tests recorded against the reference by `/rspec:verify`, listed in `acceptance/manifest.json`; read-only for the build). Criterion levels are in `<spec>/criteria.lock.json`.

## Release 1: MVP
<one line: what a user can do after this release; no feature IDs in release headings or lines>

## Slice 1: <name>
Goal: <what works end to end after this slice>

| Order | Feature | Story | Criteria | Operations | Schemas | NFRs |
|---|---|---|---|---|---|---|
| 1 | F-<CODE>-<NN> <name> | features/<file> | F-<CODE>-<NN>.AC1, F-<CODE>-<NN>.AC2 | <operationId> | <entity> | <NFR-NN> |

Done when: every criterion with a level 2 test in the bundle passes that test against the build, and every other criterion has a passing builder test.
