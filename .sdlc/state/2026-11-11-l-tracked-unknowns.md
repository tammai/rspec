# 2026-11-11-l-tracked-unknowns
Status: done
Process: 3
Change: docs/sdlc/changes/2026-11-11-l-tracked-unknowns.md   (this feature's record for people)
Track: L   (sized up because: approach unclear at the start; new registry file, a level rule in check_spec.py and six prompts/skills; footprint: 13 files)
Risk: low
Top model: opus   (fable only if the user chose it)
Commands: test: `python3 -m unittest discover tests`
Started: 2026-11-11
Base: 5ab7106
Owner: tam.mai@bigin.vn
Tool: claude-code
Verified: 5ab7106 tree 6f206c9370d35ae451be28d9c8de3b294cfb1ff9
Current: Stage 4 – Ship

## Stages
- [x] 1 Define   — the change file, the plan sections below
- [x] 2 Build
- [x] 3 Review   — the change file's ## Review
- [ ] 4 Ship     — PR: (Learn: knowledge, recurring-defects.md)

## How the build runs
inline

## Handoff
- precedent: check_departures and its si>=5 handoff test, scripts/check_spec.py:126-154 and :334; write_lock levels :157-215
- in_scope(prio, cfg) and criteria(spec) in scripts/rspec_lib.py; contracts.parse_yaml / YamlError for the YAML subset
- lock must keep C3 shape: no new fields; contracts.check_lock runs in write_lock

## Tasks
1. **Registry check and level cap** — AC-001 AC-002 AC-003 AC-004 AC-005
   - Files: `scripts/check_spec.py`, `tests/test_unknowns.py`
2. **Prompts, skills, template, docs** — AC-006
   - Files: `agents/story-writer.md`, `skills/stories/SKILL.md`, `skills/audit/SKILL.md`, `skills/amend/SKILL.md`, `skills/handoff/SKILL.md`, `templates/build-plan.md`, `references/writing-rules.md`, `README.md`, `CHANGELOG.md`, `docs/sdlc/changes/2026-11-11-l-tracked-unknowns.md`

## Public Surface
- none

## Gate log
- 2026-11-11 Stage 1: pass — plan approved by the user (L): AskUserQuestion Approve after the builder check
- 2026-11-11 Stage 2: pass
- 2026-11-11 review: ran code (L), self-chosen: L
- 2026-11-11 Stage 3: fail — review r1 FAIL: H1 H2 H3 H4 H5 M1 (+M2 M3 bugs, F1-F3, L2 L3 in passing)
- 2026-11-11 Stage 2: pass
- 2026-11-11 Stage 3: pass — review r2 PASS; fixing its low bugs L-a L-b L-c without another round
- 2026-11-11 Stage 2: pass
- 2026-11-11 Stage 3: pass

## Deviations
- 2026-11-11 change file What: AC-005 (no registry changes nothing) became a must-never-break line keeping its test. Why: it passes before the code exists, so it can't be red; it's a regression guard, not new behaviour. Effect: ACs are 001-004 and 006.
- 2026-11-11 check_unknowns What: new function in scripts/check_spec.py beside check_departures. Why: the Design's registry check; internal to the script (no other caller). Effect: none outside check_spec.py.
- 2026-11-11 write_lock What: takes a new capped argument ({criterion: [open U-ids]}). Why: the level cap of AC-001; its only caller is check_spec.py main(). Effect: none outside check_spec.py.
- 2026-11-11 check_spec.py What: U- links are read only from '- U-<nnn>:' lines in a story's ## Open questions, not from any U-nnn token in stories and features.md as the Design says. Why: review r1 M2: example data in criteria (e.g. a product's U-123 keys) would have errored in specs without unknowns.yaml, breaking must-never-break 1. Effect: AC-004 holds for the lines step 3 writes; a U- token elsewhere is not a link.
- 2026-11-11 check_spec.py What: unknown keys in an entry are errors (UNKNOWN_KEYS); a named feature is checked against features.md, not story files. Why: review r1 M3 (constitution IV) and H1. Effect: stricter registry; Drop/Later features can be named.

## Open questions
-
