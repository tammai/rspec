<!-- rspec:handoff -->
## Building <working name> from the spec

The spec in `<spec>/` (contracts in `<contracts>/`, ADRs in `<decisions>/`) is the source of truth for this rebuild.

- Work slice by slice in `<spec>/build-plan.md` order. Before a feature, set `status: in-progress` in its story frontmatter; set `done` when all its acceptance criteria pass.
- Each acceptance criterion (Given / When / Then) gets one test, named after its ID (`F-ISS-01.AC2`); cite criterion IDs in commits and notes and never restate the criterion text. Failure modes get a test only when they protect data or permissions.
- Acceptance tests in `<spec>/acceptance/` (recorded against the reference by `/rspec:verify`) are read-only: a test that looks wrong is a spec question for `/rspec:amend`, never an edit. Run them against the build with `ACCEPT_BASE_URL` set to it: `python3 <plugin root>/contracts/v1/contracts.py run-http <spec>/acceptance/http/*.yaml` and `npx playwright test <spec>/acceptance/e2e`.
- A slice is done when every criterion with a level 2 test in `<spec>/criteria.lock.json` passes that test against the build, and every other criterion has a passing test of your own.
- API code follows `<contracts>/openapi.json`; data types follow `<contracts>/schemas/`. Change the contract first, then the code.
- ADRs in `<decisions>/` marked Accepted are binding. To change one, write a new ADR that supersedes it.
- If `<spec>/production-readiness.md` exists, nothing ships to production until every item in it is checked, with its evidence after the item.
- Do not use the original product's name, logo, text or images.
- After changing anything in `<spec>/`, `<contracts>/` or `<decisions>/`, run `python3 <plugin root>/scripts/check_spec.py .` and add a line to `<changelog>`.
<!-- /rspec:handoff -->
