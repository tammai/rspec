# Spec: sdlc 3.5.0, test integrity and spec-backed changes

2026-11-08 · @Tam Mai · draft for sign-off · depends on contracts v1 ([01](01-shared-contracts.md))

## Problem

sdlc 3.4.0 proves each AC with a test recorded red then green, verifies the full suite, and reviews in fresh contexts. What it does not check:

1. **Whether a test actually proves its AC.** Red → green shows the test failed without the code and passes with it. A test that asserts only that a function exists, or asserts loosely, passes the same way. A low-risk M gets no review at all.
2. **Whether a test changed after the red step.** A builder with a red build can weaken an assertion; `$V` still passes.
3. **Correlation.** The same context writes the tests and the code, so a misread AC is built and tested the same wrong way.
4. **Running behaviour.** `qa-tester` runs only at a backlog's Feature close or on request; a single-part M or L that adds an endpoint is never run as a user would.
5. **Rendering.** `ui-reviewer` reads the diff; screenshots only when asked.
6. **Test level.** Nothing stops a user-visible AC from being proved by a unit test with mocks.
7. **Spec-backed work.** Against an rspec spec, the change file restates criteria, trace works per story, and builders write their own tests even when recorded ones exist.

## Decisions

| Question | Decision |
|---|---|
| Scope by track | S unchanged. New checks scale with track and risk; see the table below. |
| Spec-backed mode trigger | A change whose ACs cite IDs found in a `criteria.lock.json` in the repo (or a path in `.sdlc/config.json` → `spec_lock`). No flag. |
| Mutation testing **(sign-off D6)** | L or high risk, changed lines only, 10-minute cap, stack tool from setup (`stryker`, `mutmut`, `go-mutesting`, `cargo-mutants`, …). Tool missing → `not run`, reported, never a pass. |

| Check | S | M low | M high | L |
|---|---|---|---|---|
| C1 example data (S1) | — | warning | error | error |
| Source tags (S1) | — | only non-`[request]` | all | all |
| Test lock (S4) | yes | yes | yes | yes |
| test-auditor (S5) | — | yes | yes | yes |
| Mutation probe (S6) | — | — | yes | yes |
| Separate test-writer (S7) | — | — | — | yes |
| qa-tester on surface (S8) | — | yes | yes | yes |
| UI render (S9) | — | on `areas.ui` | on `areas.ui` | on `areas.ui` |

## Requirements

### S1 Criterion grammar in Define

- Define writes ACs per contracts C1. The low-risk M rule "write it straight off" stays, with one addition: each AC's `then` names the value a test will assert.
- Source tags per the track table. L self-approval gains a fifth check: no `[decision]` AC that the user could weigh differently; one found → ask, as for any failed check.
- `verify.py` lints ACs through the vendored `contracts.py` at the track's level.

### S2 Spec-backed change files

- An AC cites a criterion and does not restate it: `- **AC-003** → F-ISS-01.AC2`. `brief.py` and the gate message print the criterion text from the lock, so the human still reads it.
- `verify.py trace` in this mode checks: every cited ID exists in the lock; its `text_sha256` equals the value recorded at Define (stored in `<state>`); every criterion assigned to the current slice (`$S new … --criteria <ids>` or the build-plan slice) is cited or listed under `## Out of scope` with a reason. A changed hash → `stale criterion`, Build stops and asks.
- The 10-AC guideline counts cited criteria.

### S3 External acceptance tests

- When `acceptance/manifest.json` has an `open` test for a cited criterion, its Acceptance tests row uses it: Test = the bundle path, Run = the runner command with `ACCEPT_BASE_URL` pointing at the local build (setup records the start command and URL in config as `accept.start`, `accept.base_url`).
- The red step runs it against the unbuilt feature like any other test.
- The PreToolUse hook denies Write/Edit/Bash writes on paths in the manifest. A wrong recorded test is a question (S10), never an edit.
- Criteria without a recorded test fall back to builder-written tests, which the test lock (S4) covers.

### S4 Test lock

- `verify.py red` stores the SHA-256 of each test file it ran, in `<state>` under `## Test lock`.
- `$V` fails when a locked file changed, unless `<state>` has a deviation line `test-change <file> What: … Why: …` **and** the affected ACs were re-run through `red` against the base commit (`verify.py red --at <Base> AC-…`, run in a temporary worktree) and failed there.
- New test files are free. Deleting a locked file is a change.

### S5 test-auditor

New agent `sdlc:test-auditor` (sonnet tier, read-only, fresh context), run after Build's `$V` passes and before the reviews start: it is cheap, and a weak test would make every later review rest on a false green.

- Input: `<change>` ACs (with criterion text in spec-backed mode) and the test files from the Acceptance tests table. It does **not** read source files or the diff.
- Per AC it answers: does the test assert the `then`? with the AC's example data? on a specific outcome (not truthiness or "no error")? at the declared level? Each "no" is a finding with the line.
- Findings are `high` (they fail an AC's proof). Back to Build: strengthen the test, then a mutation probe for that AC (S6) shows the strengthened test fails when the behaviour is broken. Round cap as for reviews.
- In spec-backed mode, recorded tests are skipped (rspec's verify already proved them against the reference).

### S6 Mutation probe

- M high and L: run the setup-recorded mutation command scoped to lines changed since Base, 10-minute cap. A surviving mutant on a line an AC test covers → finding: `high` when the line is in code a must-never-break line names, else `medium`. Results go in `## Review`.
- S5's per-AC probe: the auditor proposes one minimal mutation that should break the AC; the orchestrator applies it in a temporary worktree, runs the AC's test, expects red. Green → the test is still too weak.

### S7 Separate test-writer on L

On L, a fresh `sdlc:test-writer` agent (sonnet) writes every builder-written AC test from `<change>` alone, then the red step runs. The builder writes code and may not edit those tests (S4 applies from the red step). Not on M: the extra context costs more than the correlation it removes at that size.

### S8 qa-tester on surface

Add a row to the review table: **QA** fires when `## Public Surface` is not `- none` or the diff touches `areas.ui`. `qa-tester` runs in parallel with the other chosen reviews, same budget and black-box rules as today. Its failed scenarios are `high`. In spec-backed mode its scenarios are the cited criteria plus their failure modes, and it writes `finding-v1` files as well as its report.

### S9 UI render

When `areas.ui` is touched and a browser tool is available, `ui-reviewer` gets screenshots at 375, 768 and 1440 px, plus dark mode when the design system defines it, taken by the orchestrator from the running build. No browser tool → the review says `not rendered`.

### S10 Spec questions

When a builder finds a cited criterion ambiguous, wrong, or untestable as written:

- Standalone: ask the user, as today.
- Spec-backed: `$S question <f> <criterion> "<question>"` writes `.sdlc/.work/spec-questions/<feature>.json` (a `finding-v1` with `source: sdlc-question`, `class: spec-gap`, routed without a verifier per C6's exception, contracts ≥ 1.1.0), blocks the backlog part, and the run continues with other ready parts. The orchestrator (product-rebuild, or rspec's pipeline driving sdlc) answers through `/rspec:amend`; the part unblocks when the lock shows the new hash.

### S11 Test level

The Acceptance tests table gains a `Level` column (`unit|integration|e2e|manual`). `verify.py` warns when an AC whose `then` names a screen, a response, a command output or a stored record is proved only at `unit`. The code-review brief includes the rule.

### S12 Setup

`/sdlc:setup` records, per package: the mutation command (offers one per stack, installs nothing), `accept.start` and `accept.base_url` when a `criteria.lock.json` or `acceptance/` is present. `/sdlc:upgrade` migration adds the new config keys with empty values.

## Backlog parts

1. Vendor contracts; S1; S11; S12 config keys and migration.
2. S4 test lock in `verify.py` and the hook; S3 external tests.
3. S2 spec-backed trace and `brief.py` display; S10.
4. S5 test-auditor agent and brief; S6 mutation probe.
5. S7 test-writer; S8 review table row; S9 render.

## Acceptance

- Unit tests for each `verify.py` rule: lock mismatch, deviation + re-red path, stale criterion, slice coverage, level warning.
- Eval set (extend the existing eval): one feature with a planted weak test (`expect(fn).toBeDefined()`) → test-auditor fails it; one with a test weakened after red → `$V` fails; one spec-backed slice with recorded HTTP tests → red, build, green, no test file edited.
- Token and wall-time delta measured per track on the eval set against 3.4.0 and reported in the release notes; the M-low delta must stay under +20% tokens.
- `/sdlc:doctor` reports missing mutation tooling and missing `accept.*` keys with a fix line.
