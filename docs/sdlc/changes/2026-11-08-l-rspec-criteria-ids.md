# rspec 0.11.0: criterion IDs and verification against the reference

## Why

**Request (verbatim):** "implement docs/specs/rebuild-upgrade/02-rspec.md, part 1 only (Backlog part 1: vendor contracts v1; R1 template, story-writer, check rules, migration script; R2 criteria lock)"

The spec is the source: [02-rspec.md](../../specs/rebuild-upgrade/02-rspec.md), against shared contracts v1 (`contracts/v1/CONTRACTS.md`, C1–C5). This file is its index plus the tests. The spec's five backlog parts are B1–B5 in `.sdlc/state/2026-11-08-l-rspec-criteria-ids/backlog.md`; each part is dispatched as its own task by the rebuild-upgrade orchestrator.

**The user's words:** via the orchestrator (msg_ae7b769d541a): Q2, Differences lines without `→ D-` warn in part 1 and become an error with the dangling check in part 2 (R8). Q4, no tag or version bump in part 1, CHANGELOG `[Unreleased]` only. The user (msg_8ae9294d0727): Q1 (a), `→ TODO` failure modes from migration are WARN with `needs /rspec:stories <module>`; every other check_story/check_criteria problem, including C1 example data and grammar on legacy criteria, stays ERROR. Q3 (a), open questions go in a section after `Sources`; the stories skill reads it there and the main session empties it.

## Decisions

| Decision | Ruled out | Why |
|---|---|---|
| Contracts vendored at `contracts/v1/`, byte-identical from product-rebuild `34dd29a` (MANIFEST sha256 `6557b171…`), with `contracts/v1/** -text` in `.gitattributes` | editing or re-sealing the copy | 01 Distribution; autocrlf would break every hash |
| `check_spec.py` calls `contracts.check_story` / `check_criteria(profile="rspec", domain=…)` for every story and drops its own Gherkin and evidence-tag checks | running both | one source of the C1/C2 rules; two would report the same fault twice |
| One drift test runs `contracts.py vendor-check contracts/v1` | no drift test (global "no meta tests" rule) | 01 Acceptance requires it in each consumer |
| Lock written only when the check has no errors; `generated` kept when the criteria are unchanged | rewriting it on every run | R2 says "on every successful run"; an unchanged lock with a new timestamp is churn in every commit |
| Changed text → level 0, `test` kept, WARN `needs re-verify` | ERROR | an error would block the lock write that records the drop |
| Removed (`~~struck~~`) criteria are not in the lock | listing them | C3 hashes the active text; `check_lock` finds only active lines |
| `departures` in the lock stays `[]` in part 1 | parsing Differences | R8 (B2) owns the departures link |
| Differences lines without `→ D-<nnn>` warn (part 1) | error now | orchestrator Q2; R8 needs the registry first |
| `→ TODO` failure modes WARN `needs /rspec:stories <module>`; all other C1/C2 problems ERROR, legacy criteria included | TODO as ERROR | user Q1 (a): a migrated spec fails only on real C1 problems |
| Story-writer's `Open:` notes go in an `Open questions` section after `Sources` | notes in the Story section | user Q3 (a); C2 allows extra sections |
| Level 1 (B3): sampled + confirmed, or unsampled in a tag population whose sample has no CONTRADICTED; any criterion with its own finding stays 0; written to `audit/levels.json` with each criterion's text hash, and `check_spec.py` raises 0 → 1 only while the hash matches | levels written by the fact-checker; every population member level 1 regardless of contradictions | C3's level rule plus R4's "no finding"; figures come from a script, not an agent (02 §Acceptance) |
| 20% of a tag population rounds up; `[3p]` is not sampled (stays level 0) | rounding down; sampling `[3p]` | R4 names five tags; rounding up never samples fewer than the rule |
| Verify runners: http via `contracts.run_http`, playwright via `npx playwright test`, maestro via `maestro test` (exit code; missing tool = not run); a cli criterion stays level 1 with reason `cli runner not in contracts v1` | rspec-defined cli fields; http only | orchestrator Q7 (a): cli fields are unsettled in contracts v1 |
| Level 2 and flaky come from `verify/runs.jsonl`, written by `verify_run.py`, judged by `verify_report.py`: the last three runs on the build green with no red on it → level 2; a pass and a fail on one build → flaky. Build = `sources.commit` or `unversioned` | recorders reporting their own results | 02 §Acceptance: no agent-written figures |
| Accuracy target counts `[docs]` `[api]` `[observed]` `[code]`; `[inferred]` is reported apart (not contradicted / contradicted / decision) | counting `[inferred]` in accuracy | an inferred criterion has no source to support it, so it can only be contradicted or not |

**Proposals not asked for:** None

## Acceptance criteria

- **AC-001** 01 §Distribution, 02 part 1: Given the vendored `contracts/v1/`, when `contracts.py vendor-check contracts/v1` runs, then it reports no drift; a changed byte fails it.
- **AC-002** 02 §R1: Given a story with C1 IDs and the C2 sections, when `check_spec.py` runs, then it passes; a criterion without an ID, with bad grammar, without example data or a source tag, or a story with `## Edge cases`, is an ERROR naming the file.
- **AC-003** 02 §R1: Given the story template and `story-writer`, then they write `F-<CODE>-<NN>.AC<n>` IDs, `Failure modes`, `Must never break`, `Differences from the original` and no `Edge cases` (template placeholders still caught by `check_spec.py`).
- **AC-004** 02 §R1: Given a spec with legacy stories, when `migrate_criteria.py <spec>` runs, then each criterion gets the next free `<ID>.AC<n>` in file order, `Edge cases` lines become `Failure modes` lines ending `→ TODO`, and a second run changes no byte.
- **AC-005** 02 §R2: Given a spec that passes `check_spec.py`, then `<spec>/criteria.lock.json` is written, valid under `contracts.check_lock`; after a criterion's text changes, that criterion is level 0 and listed as `needs re-verify`, and the others keep their level.
- **AC-006** 02 §R3: handoff writes `<docs>/prd.md` from sdlc's PRD sections with links into the SRS (B2).
- **AC-007** 02 §R8: `features` approval writes `departures.yaml` entries; `check_spec.py` errors on a dangling `D-` reference and on a Differences line without one (B2).
- **AC-008** 02 §R6: `build-plan.md` lists criterion IDs per slice and the bundle path; both CLAUDE.md templates carry the cite-only and read-only rules (B2).
- **AC-009** 02 §R4: `audit_sample.py` samples `min(25, max(5, 20%))` per tag (`[docs]` `[api]` `[observed]` `[code]` `[inferred]`) with a fixed seed; after the audit, `audit_sample.py --levels` turns the fact-checker's verdicts into level 1 (C3: sampled and confirmed, or unsampled in a population whose sample has no contradiction; never a criterion with its own finding), and `check_spec.py` writes that level into the lock while the criterion's text is unchanged (B3).
- **AC-010** 02 §R5.3, §R5.6: Given a recorded HTTP test for a criterion, when `verify_run.py` runs it three times green against the reference and `verify_report.py` runs, then the criterion is level 2 in `criteria.lock.json` with its test, `acceptance/manifest.json` passes `contracts.py bundle`, and `verify/summary.md` reports the level 2 share for MVP and per module (B4).
- **AC-012** 02 §R5.5: Given a test that passes and fails on the same reference build, when the report runs, then the criterion is listed `flaky` and is not level 2 (B4).
- **AC-013** 02 §Decisions (New stage), §Acceptance: Given a spec whose audit is done, when `progress.py` runs, then `next` is `verify` (`decide` until `reference.run.kind` is set; skipped for `none`; done when `verify/summary.md` exists), so `/rspec:pipeline --until verify` stops after it (B4).
- **AC-014** 02 §Decisions (Reference access): Given `reference.run` with `writes: true` on a `url` reference, or a base URL variable not named `ACCEPT_*`, when `check_spec.py` runs, then it is an error (B4).
- **AC-015** 02 §Acceptance: the live run on `tests/fixtures/reference-app/`: `verify` reaches level 2 on every recordable criterion, the judge classifies the planted wrong criterion `spec-wrong`, the planted flaky endpoint is reported `flaky` (B4).
- **AC-011** 02 §R7: `/rspec:amend <ID> "<reason>"` edits the criterion, logs it, regenerates the lock and drops it to level 0 (B5).

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | tests/test_contracts_vendor.py › test_vendored_copy_matches_manifest | `python -m unittest discover -s tests -p test_contracts_vendor.py` |
| AC-002 | tests/test_criteria_ids.py › test_story_breaking_c1_or_c2_fails | `python -m unittest discover -s tests -p test_criteria_ids.py -k test_story_breaking_c1_or_c2_fails` |
| AC-003 | tests/test_criteria_ids.py › test_template_is_c2_and_placeholders_fail | `python -m unittest discover -s tests -p test_criteria_ids.py -k test_template_is_c2_and_placeholders_fail` |
| AC-004 | tests/test_criteria_ids.py › test_migration_assigns_ids_and_is_idempotent | `python -m unittest discover -s tests -p test_criteria_ids.py -k test_migration_assigns_ids_and_is_idempotent` |
| AC-005 | tests/test_criteria_ids.py › test_lock_written_and_changed_text_drops_to_level_0 | `python -m unittest discover -s tests -p test_criteria_ids.py -k test_lock_written_and_changed_text_drops_to_level_0` |
| AC-006 | manual | handoff skill prose (R3 adds no check rule); checked by reading skills/handoff/SKILL.md in Review |
| AC-007 | tests/test_departures.py › test_differences_link_to_departures_registry, test_proposed_departure_warns_until_handoff | `python -m unittest discover -s tests -p test_departures.py` |
| AC-008 | tests/test_build_plan_criteria.py › test_slice_lists_its_criterion_ids | `python -m unittest discover -s tests -p test_build_plan_criteria.py` |
| AC-009 | tests/test_audit.py › test_sample_size_per_tag, test_audit_verdicts_raise_criteria_to_level_1 | `python -m unittest discover -s tests -p test_audit.py` |
| AC-010 | tests/test_verify.py › test_three_greens_reach_level_2 | `python -m unittest discover -s tests -p test_verify.py -k test_three_greens_reach_level_2` |
| AC-012 | tests/test_verify.py › test_pass_and_fail_on_one_build_is_flaky | `python -m unittest discover -s tests -p test_verify.py -k test_pass_and_fail_on_one_build_is_flaky` |
| AC-013 | tests/test_verify.py › test_verify_step_sits_between_audit_and_handoff | `python -m unittest discover -s tests -p test_verify.py -k test_verify_step_sits_between_audit_and_handoff` |
| AC-014 | tests/test_verify.py › test_reference_run_rules | `python -m unittest discover -s tests -p test_verify.py -k test_reference_run_rules` |
| AC-015 | manual | live agent run (approved, about 0.45M tokens), results in the part's report |
| AC-011 | manual | test written in B5, which replaces this row |

## Must never break

- A spec without stories (stage init–features) passes `check_spec.py` as before.
- The vendored `contracts/v1/` is never edited; only a re-vendor from the canonical repo changes it.
- `criteria.lock.json` is never written by a failing check, so a lock always matches a passing spec.

## Failure modes

- A legacy spec (no IDs, `Edge cases`) is checked → AC-002 errors point to `migrate_criteria.py`; AC-004.
- Migration run twice, or on a partly migrated spec → AC-004 (idempotent, numbering never reuses an ID).
- A criterion edited after verification → AC-005.
- Windows checkout with `core.autocrlf` → AC-001 (`-text` attribute).

## Out of scope

- B2–B5 content beyond the index above; each part fills its own tests.
- Fixing existing specs' criteria content (example data, grammar): that is the next `stories` pass.

## Open questions

- none (Q1–Q4 answered; see Decisions)
