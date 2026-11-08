# Spec: rspec 0.11.0, criterion IDs and verification against the reference

2026-11-08 · @Tam Mai · draft for sign-off · depends on contracts v1 ([01](01-shared-contracts.md))

## Problem

rspec 0.10.1 produces a well-structured SRS and audits it with three independent agents, but the audit checks the spec against **sources**, never against the **running product**:

- The fact-checker samples 25 `[docs]` and 25 `[api]` criteria. `[observed]` and `[inferred]` criteria, the riskiest, are never sampled.
- Criteria stay prose until a builder writes tests for them. A wrong criterion that matches outdated docs passes audit and gets built.
- Criteria have no IDs of their own, so downstream trace works per story.
- Handoff asks sdlc to draft a PRD from rspec files, creating a second summary of the same content.
- `Edge cases` is free text that may never become a test.

A spec handed to any builder (sdlc, Claude Code, a human team) should state how much of it was proved against the product.

## Decisions

| Question | Decision |
|---|---|
| Where verification lives | In rspec, as levels (contracts C3). product-rebuild consumes the levels; it does not re-verify. |
| New stage | `/rspec:verify`, after `audit`, before `handoff`. Optional: the pipeline asks once (autopilot: `rules.verify`). Without it, every criterion stays at level ≤ 1 and the spec says so. |
| Reference access | New `reference.run` block in `rspec.json`: `kind` (`local` · `url` · `none`), `base_url_env`, `accounts` (env var names only), `writes` (`true` only for `local`), `start`/`stop` commands for `local`. |
| Closed SaaS | `kind: url`, `writes: false`: only read-only criteria are recorded; criteria needing a write stay level 1 with reason `read-only reference`. Recording respects the product's terms; `init` repeats the legal note. |
| Who fixes a disputed criterion | A fresh `verify-judge` agent, never the recorder that hit the failure. |

## Requirements

### R1 Criterion IDs and story sections

- Story template and `story-writer` adopt contracts C1/C2: `F-<CODE>-<NN>.AC<n>` IDs, `Failure modes`, `Must never break`, departure links. `Edge cases` is removed from the template.
- `scripts/migrate_criteria.py <spec>` assigns IDs to an existing spec in file order, converts `Edge cases` lines into `Failure modes` lines marked `→ TODO` for the next `stories` pass, and is idempotent.
- `check_spec.py` enforces C1 via the vendored `contracts.py` (example-data rule at error level) and the C2 sections.

### R2 Criteria lock

`check_spec.py` writes `<spec>/criteria.lock.json` (C3) on every successful run. A criterion whose text changed since the last lock drops to level 0 and is listed in the check output as `needs re-verify`.

### R3 PRD without a second summary

When the build engine is sdlc, `handoff` writes `<docs>/prd.md` itself from sdlc's `templates/prd-template.md` sections, each section a short paragraph plus links into the SRS (`features.md`, `nfr.md`, `README.md`). It tells `/sdlc:setup` that a PRD exists at that path (setup's "a PRD already exists" path: use as is). The instruction to draft a PRD from rspec files is deleted.

### R4 Audit covers every tag

`audit_sample.py` samples per tag with a fixed seed: `min(25, max(5, 20%))` criteria for each of `[docs]`, `[api]`, `[observed]`, `[code]`, `[inferred]`.

- `[observed]`: the fact-checker re-observes read-only through Playwright when `reference.run.kind` is not `none`; otherwise it checks the research note that recorded the observation.
- `[inferred]`: the fact-checker answers one question per criterion: does a source contradict it, and should it be a decision for the user? The second becomes a parked decision under autopilot.
- Targets unchanged (accuracy ≥ 90% with none contradicted, coverage ≥ 90%, no Important contradictions). A criterion in a sampled population with no finding gets level 1.

### R5 `/rspec:verify` (level 2)

Runs only when `reference.run.kind` is `local` or `url`.

1. **Preflight** (main session): start the reference (`local`), check `base_url_env` answers, check each account variable is set. Any failure → stop with the failing item; never record against a half-working reference.
2. **Seed** (one `reference-seeder` agent, sonnet): reads every in-scope criterion's `Given` and writes `acceptance/seed/` so each example value exists (team ENG with 11 issues). `writes: false` → no seeding; criteria whose `Given` needs data the reference lacks stay level 1 with reason `unseedable`.
3. **Record** (one `criterion-recorder` agent per module, sonnet, at most 4 in parallel): for each criterion, pick the runner by surface (API → `http`, UI → `playwright`, mobile → `maestro`, CLI → `cli`), write the test in contracts C4 format, run it against the reference. Green three times in a row → level 2. A recorder gets the story, `domain.md`, the contracts and the seed; it may not edit any spec file.
4. **Disputes**: a criterion whose test stays red after 3 attempts is passed to a fresh `verify-judge` (opus) with the criterion, the test, and the reference's actual responses or screenshots, not the recorder's reasoning. The judge returns one of: `spec-wrong` (proposes corrected text, main session applies it through R7 and re-records), `test-wrong` (one more recorder attempt with the judge's note), `unrecordable` (level 1 with reason).
5. **Flakes**: a test that passes and fails on the same reference build is `flaky`, kept out of level 2, listed in the report.
6. **Report**: `<spec>/verify/summary.md`, generated by script: level 2 share for MVP and for all in-scope criteria, per module; disputes and their outcomes; unrecordable reasons. Targets: MVP ≥ 90% level 2 for `local`; report-only for `url`.

Cost controls: verify records only criteria of features in scope (MVP and Later in the build plan); it reuses one authenticated browser state per account; recorders stop a criterion after 3 attempts; the judge runs only on disputes. `--only <feature IDs>` re-verifies a subset.

### R6 Handoff consumes the levels

- `build-plan.md` lists criterion IDs per slice (not only story files) and the bundle path.
- The slice "done when" rule: every criterion with a level 2 test passes that test against the build; every other criterion has a builder test.
- `templates/claude-md-sdlc.md`: change files cite criterion IDs only and never restate the text (sdlc spec-backed mode, [03](03-sdlc.md) S2); acceptance tests from the bundle are read-only.
- `templates/claude-md.md` (Claude Code without sdlc): the same two rules, plus "run `contracts.py run-http` / `npx playwright test acceptance/e2e` against the build".

### R7 `/rspec:amend` for changes after handoff

`/rspec:amend <criterion ID> "<reason>"`: edits the criterion (or adds a new one), writes a changelog line, regenerates the lock, drops the criterion to level 0, re-runs `verify --only` for its feature when a reference is configured. Accepts a `finding-v1` file as input (route `rspec`) and records the finding ID in the changelog. This is the only path for a builder's spec question to change the spec.

### R8 Departures

`Differences from the original` lines reference `departures.yaml` entries (C5). `features` approval writes a `D-<nnn>` entry for each Drop or simplification the user accepts. `check_spec.py` errors on a dangling `D-` reference.

## Standalone behaviour

- Without sdlc or product-rebuild: R1, R2, R4, R8 apply; R5 is offered when a reference is configured; R6 writes the Claude Code variant.
- Existing specs: run `migrate_criteria.py`, then `/rspec:pipeline continue`; nothing else breaks.

## Backlog parts

1. Vendor contracts v1; R1 (template, story-writer, check rules, migration script); R2.
2. R3, R8, R6 template changes.
3. R4 audit sampling and fact-checker changes.
4. R5 agents (`reference-seeder`, `criterion-recorder`, `verify-judge`), `verify` skill, `progress.py` stage, report script.
5. R7 amend skill.

## Acceptance

- Unit tests for every new check rule, the lock, migration idempotence, per-tag sampling, and the report generator (no agent-written figures).
- A fixture product (small HTTP app in `tests/fixtures/reference-app/`, runnable with `python3 -m`) with 3 features: `verify` reaches level 2 on all recordable criteria; one planted wrong criterion is classified `spec-wrong` by the judge; one planted flaky endpoint is reported `flaky`.
- Re-run on the gophish → bigin-phish spec: audit targets still met; `verify` level 2 share reported.
- `/rspec:pipeline` resumes across every new stage; `--until verify` stops there.
