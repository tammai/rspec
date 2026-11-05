<!-- rspec:handoff -->
## Building <working name> from the spec

The spec in `docs/` is the source of truth for this rebuild.

- Work slice by slice in `docs/build-plan.md` order. Before a feature, set `status: in-progress` in its story frontmatter; set `done` when all its acceptance criteria pass.
- Each acceptance criterion (Given / When / Then) gets one test. Edge cases get a test only when they protect data or permissions.
- API code follows `docs/openapi.json`; data types follow `docs/schemas/`. Change the contract first, then the code.
- ADRs in `docs/decisions/` marked Accepted are binding. To change one, write a new ADR that supersedes it.
- Do not use the original product's name, logo, text or images.
- After changing anything in `docs/`, run `python3 <plugin root>/scripts/check_spec.py .` and add a line to `CHANGELOG.md`.
<!-- /rspec:handoff -->
