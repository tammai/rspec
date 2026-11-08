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
- **AC-009** 02 §R4: `audit_sample.py` samples `min(25, max(5, 20%))` per tag with a fixed seed (B3).
- **AC-010** 02 §R5, §Acceptance: `/rspec:verify` on `tests/fixtures/reference-app/` reaches level 2 on recordable criteria, classifies the planted wrong criterion `spec-wrong` and reports the flaky one; `summary.md` is script-generated; `/rspec:pipeline --until verify` stops there (B4).
- **AC-011** 02 §R7: `/rspec:amend <ID> "<reason>"` edits the criterion, logs it, regenerates the lock and drops it to level 0 (B5).

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | tests/test_contracts_vendor.py › test_vendored_copy_matches_manifest | `python -m unittest discover -s tests -p test_contracts_vendor.py` |
| AC-002 | tests/test_criteria_ids.py › test_story_breaking_c1_or_c2_fails | `python -m unittest discover -s tests -p test_criteria_ids.py -k test_story_breaking_c1_or_c2_fails` |
| AC-003 | tests/test_criteria_ids.py › test_template_is_c2_and_placeholders_fail | `python -m unittest discover -s tests -p test_criteria_ids.py -k test_template_is_c2_and_placeholders_fail` |
| AC-004 | tests/test_criteria_ids.py › test_migration_assigns_ids_and_is_idempotent | `python -m unittest discover -s tests -p test_criteria_ids.py -k test_migration_assigns_ids_and_is_idempotent` |
| AC-005 | tests/test_criteria_ids.py › test_lock_written_and_changed_text_drops_to_level_0 | `python -m unittest discover -s tests -p test_criteria_ids.py -k test_lock_written_and_changed_text_drops_to_level_0` |
| AC-006 | manual | test written in B2, which replaces this row |
| AC-007 | manual | test written in B2, which replaces this row |
| AC-008 | manual | test written in B2, which replaces this row |
| AC-009 | manual | test written in B3, which replaces this row |
| AC-010 | manual | test written in B4, which replaces this row |
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
