# 2026-11-17-m-lock-lf-readonly
Status: done
Process: 3
Change: docs/sdlc/changes/2026-11-17-m-lock-lf-readonly.md   (this feature's record for people)
Track: M   (sized up because: —; footprint: 6 files)
Risk: low
Top model: opus   (fable only if the user chose it)
Commands: test: `python3 -m unittest discover tests`
Started: 2026-11-17
Base: 3612c3c
Owner: tammai.it@gmail.com
Tool: claude-code
Verified: 3612c3c tree a593b0c1fa3a9f559add94ad61c77909d3b83068
Current: Stage 4 – Ship

## Stages
- [x] 1 Define   — the change file, the plan sections below
- [x] 2 Build
- [x] 3 Review   — the change file's ## Review
- [ ] 4 Ship     — PR: (Learn: knowledge, recurring-defects.md)

## How the build runs
inline: this session builds it, one part

## Handoff
- lock write: scripts/check_spec.py:312-313; option parsing: scripts/check_spec.py:324-327

## Tasks
1. **Init writes .gitattributes** — AC-001
   - Files: `scripts/init_spec.py`, `tests/test_init.py`
2. **check_spec --no-lock** — AC-002
   - Files: `scripts/check_spec.py`, `tests/test_criteria_ids.py`, `skills/check/SKILL.md`
3. **Recorder hydration rule and changelog** — AC-003
   - Files: `agents/criterion-recorder.md`, `CHANGELOG.md`

## Public Surface
- command `check_spec.py --no-lock` — AC-002

## Test lock
- `tests/test_criteria_ids.py` sha256:0c54be06121a2e1b95ae4f962e2436bca25bf4fbab7801fa3a1fe47eabf59e23
- `tests/test_init.py` sha256:009e923669334e290cdecb4dfa0c7d6ce38c6b2fd44f4d5054f52885f9328ab0

## Gate log
- 2026-11-17 Stage 1: pass — plan not stopped for approval: low-risk M
- 2026-11-17 Stage 2: pass
- 2026-11-17 review: ran code (Public Surface not none), not asked: low risk
- 2026-11-17 Stage 2: pass
- 2026-11-17 Stage 2: pass
- 2026-11-17 Stage 3: pass

## Deviations
- 2026-11-17 test-change tests/test_criteria_ids.py What: --no-lock now must exit 1 on an out-of-date lock; added a CRLF self-heal test. Why: review r1 (stale lock passed a gate; CRLF checkout never healed).
- 2026-11-17 test-change tests/test_init.py What: also asserts a fresh init creates .gitattributes. Why: review r1, the created branch was untested.
- 2026-11-17 scripts/rspec_lib.py What: pin_lock_lf shared by init and check_spec. Why: review r1, rerunning init on an existing spec is unsafe, so check_spec pins the line from the real spec path. Effect: existing specs get the line on their next check.
- 2026-11-17 write_lock What: takes write=True instead of reading --no-lock from sys.argv. Why: review r1, hidden argv dependency. Effect: callers that omit it write as before.
- 2026-11-17 test-change tests/test_criteria_ids.py tests/test_init.py What: --no-lock fails on CRLF bytes and refuses --mark-tech; unwritable .gitattributes is a warning; init reports an appended .gitattributes as updated. Why: review r2.

## Open questions
-
