# 2026-11-17-s-lock-change-notice
Status: done
Process: 3
Track: S   (footprint: 3 files)
Risk: low
Top model: opus
Base: 827bdd5
Owner: tammai.it@gmail.com
Tool: claude-code
Verified: 827bdd5 tree ca8e883fd2045e0d387d706efafdc6148b27f5b6
Current: Stage 4 – Ship

## Tasks
1. **Announce lock content changes** — AC-001
   - Files: `scripts/check_spec.py`, `tests/test_criteria_ids.py`, `CHANGELOG.md`

## Public Surface
- none

## Gate log
- 2026-11-17 Stage 1: pass
- 2026-11-17 Stage 2: pass — no review: no trigger fired

## Deviations
- 2026-11-17 lock_changes What: new module-level helper in check_spec.py that names what differs between two locks. Why: keeps write_lock short. Effect: internal to check_spec.py; no other caller.

## Open questions
-
