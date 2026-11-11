# 2026-11-11-m-evidence-trust
Status: done
Process: 3
Change: docs/sdlc/changes/2026-11-11-m-evidence-trust.md   (this feature's record for people)
Track: M   (sized up because: —; footprint: 10 files)
Risk: low
Top model: opus   (fable only if the user chose it)
Commands: test: `python -m unittest discover tests`
Started: 2026-11-11
Base: 961c0bd
Owner: tam.mai@bigin.vn
Tool: claude-code
Verified: 961c0bd tree d23c78a0f696534e5c27b967a8d775afd1512b38
Current: Stage 4 – Ship

## Stages
- [x] 1 Define   — the change file, the plan sections below
- [x] 2 Build
- [ ] 3 Review   — the change file's ## Review
- [ ] 4 Ship     — PR: (Learn: knowledge, recurring-defects.md)

## How the build runs
inline

## Handoff
- level rule: scripts/audit_sample.py:17 CONFIRMED and :75 population rule; NOT-CONTRADICTED is only the [inferred] verdict (agents/fact-checker.md:33)
- contracts/v1 is vendored and hash-checked (tests/test_contracts_vendor.py): never edit it

## Tasks
1. **Levels exclude inferred** — AC-001 AC-002
   - Files: `scripts/audit_sample.py`, `tests/test_audit.py`
2. **Absence rule** — AC-003
   - Files: `references/writing-rules.md`, `references/discovery-checklist.md`, `agents/module-explorer.md`, `agents/coverage-auditor.md`
3. **Research question checklist** — AC-004
   - Files: `templates/research-module.md`, `agents/module-explorer.md`
4. **Docs and changelog** — AC-005
   - Files: `skills/audit/SKILL.md`, `agents/fact-checker.md`, `CHANGELOG.md`, `docs/sdlc/changes/2026-11-11-m-evidence-trust.md`

## Public Surface
- none

## Gate log
- 2026-11-11 Stage 1: pass — plan not stopped for approval: low-risk M
- 2026-11-11 Stage 2: pass — no review: no trigger fired

## Deviations
- 2026-11-11 env What: .sdlc/config.json test command calls python, absent from this shell's PATH (only python3). Why: run the command exactly as written. Effect: verify.py ran with a python->python3 symlink prepended to PATH; config unchanged.

## Open questions
-
