# 2026-11-11-m-unknowns-review-tickets
Status: done
Process: 3
Change: docs/sdlc/changes/2026-11-11-m-unknowns-review-tickets.md   (this feature's record for people)
Track: M   (sized up because: —; footprint: 6 files)
Risk: low
Top model: opus   (fable only if the user chose it)
Commands: test: `python3 -m unittest discover tests`
Started: 2026-11-11
Base: 7e121e5
Owner: tam.mai@bigin.vn
Tool: claude-code
Verified: 7e121e5 tree 38cdf62cd03c2f84d2c5eff3309c1a57ae65111b
Current: Stage 4 – Ship

## Stages
- [x] 1 Define   — the change file, the plan sections below
- [x] 2 Build
- [ ] 3 Review   — the change file's ## Review
- [ ] 4 Ship     — PR: (Learn: knowledge, recurring-defects.md)

## How the build runs
inline

## Handoff
- write_lock runs only 'if not errors' in main(), scripts/check_spec.py near the end; check_unknowns' handoff error is the one to exempt

## Tasks
1. **Departures encoding** — AC-001
   - Files: `scripts/check_spec.py`, `tests/test_departures.py`
2. **Capped lock at handoff, shared link scanner** — AC-002
   - Files: `scripts/check_spec.py`, `tests/test_unknowns.py`
3. **Tickets and changelog** — AC-001 AC-002
   - Files: `docs/sdlc/todo.md`, `CHANGELOG.md`, `docs/sdlc/changes/2026-11-11-m-unknowns-review-tickets.md`

## Public Surface
- none

## Gate log
- 2026-11-11 Stage 1: pass — plan not stopped for approval: low-risk M
- 2026-11-11 Stage 2: pass — no review: no trigger fired

## Deviations
- 2026-11-11 check_unknowns What: takes an H callback for its handoff error. Why: AC-002, main() writes the lock when every error came through H. Effect: none outside check_spec.py.
- 2026-11-11 report_unlisted What: new helper shared by check_departures and check_unknowns. Why: ticket L4. Effect: same messages; internal to check_spec.py.

## Open questions
-
