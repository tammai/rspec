# 2026-11-16-m-reference-adapter
Status: done
Process: 3
Change: docs/sdlc/changes/2026-11-16-m-reference-adapter.md   (this feature's record for people)
Track: M   (sized up because: —; footprint: 7 files)
Risk: low
Top model: opus   (fable only if the user chose it)
Commands: test: `python3 -m unittest discover tests`
Started: 2026-11-16
Base: a50f400
Owner: tammai.it@gmail.com
Tool: claude-code
Verified: a50f400 tree 543fb020675d6e0770a38955e67ac9923acbad88
Current: Stage 4 – Ship

## Stages
- [x] 1 Define   — the change file, the plan sections below
- [x] 2 Build
- [x] 3 Review   — the change file's ## Review
- [ ] 4 Ship     — PR: (Learn: knowledge, recurring-defects.md)

## How the build runs
inline

## Handoff
- verify_run.py main sets the test env at scripts/verify_run.py:115-127
- check_spec reference.run rules at scripts/check_spec.py:349-360

## Tasks
1. **Adapter URL, path check and down check** — AC-001 AC-002 AC-003
   - Files: `scripts/verify_run.py`, `tests/test_verify.py`
2. **check_spec adapter rules** — AC-004
   - Files: `scripts/check_spec.py`
3. **Skill and agents** — AC-005
   - Files: `skills/verify/SKILL.md`, `agents/criterion-recorder.md`, `agents/reference-seeder.md`, `CHANGELOG.md`

## Public Surface
- none

## Gate log
- 2026-11-16 Stage 1: pass — plan not stopped for approval: low-risk M
- 2026-11-16 Stage 2: pass
- 2026-11-16 review: ran code (new config key reference.run.adapter), not asked: low risk
- 2026-11-16 Stage 2: pass
- 2026-11-16 Stage 2: pass
- 2026-11-16 Stage 3: pass

## Deviations
- 2026-11-16 scripts/verify_run.py off_contract What: a new module function. Why: the path check reads the test and its seeds before any run. Effect: internal to verify_run.py; no command or flag changes.
- 2026-11-16 tests/test_verify.py What: the adapter tests use GET /api/tasks, not /api/stats. Why: the fixture's /api/stats answers 503 every second call on purpose (the flaky test). Effect: none on the code; red was recorded first with /api/stats against the unfixed code.
- 2026-11-16 Public Surface config reference.run.adapter — AC-001 AC-002 AC-003 AC-004 What: a new rspec.json key. Why: the design's point 5. Effect: optional; absent, verify is unchanged.
- 2026-11-16 scripts/rspec_lib.py adapter_problems, agents/verify-judge.md What: a shared adapter shape check and a judge rule. Why: review round 1 (H-2: verify_run.py runs before check_spec.py; H-3: the judge must not amend a criterion to an adapter fault). Effect: one rule for both scripts; adapter faults become unrecordable adapter: verdicts.

## Open questions
-
