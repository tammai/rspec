# 2026-11-15-m-verify-cost
Status: done
Process: 3
Change: docs/sdlc/changes/2026-11-15-m-verify-cost.md   (this feature's record for people)
Track: M   (sized up because: —; footprint: 8 files)
Risk: low
Top model: opus   (fable only if the user chose it)
Commands: test: `python3 -m unittest discover tests`
Started: 2026-11-15
Base: 111d719
Owner: tammai.it@gmail.com
Tool: claude-code
Verified: 111d719 tree 9373d9653360b30f9d51c8c89a6ec858a55dbfdc
Current: Stage 4 – Ship

## Stages
- [x] 1 Define   — the change file, the plan sections below
- [x] 2 Build
- [x] 3 Review   — the change file's ## Review
- [ ] 4 Ship     — PR: (Learn: knowledge, recurring-defects.md)

## How the build runs
inline, this session

## Handoff
- verify_run.run_once truncates UI output at verify_run.py:43; status() at verify_report.py:26 decides level 2 and flaky
- product-rebuild 3.2.0's step 0 prints rspec:verify --only <criterion IDs> and needs this release

## Tasks
1. **verify_run: full failing output, unreachable stops, test hash, npx via which** — AC-001 AC-002
   - Files: `scripts/verify_run.py`
2. **verify_report: flaky on the current test version, --plan with scope and only** — AC-003 AC-004
   - Files: `scripts/verify_report.py`, `scripts/check_spec.py`, `tests/test_verify.py`
3. **Skill and agent text, release 0.13.0** — AC-004
   - Files: `skills/verify/SKILL.md`, `agents/criterion-recorder.md`, `agents/verify-judge.md`, `.claude-plugin/plugin.json`, `CHANGELOG.md`

## Public Surface
- command `verify_report.py --plan` — AC-004
- config `rspec.json verify_scope` — AC-004

## Gate log
- 2026-11-15 Stage 1: pass — plan not stopped for approval: low-risk M
- 2026-11-15 review: ran code (Public Surface: verify_report.py --plan, rspec.json verify_scope), not asked: low risk
- 2026-11-15 Stage 2: pass
- 2026-11-15 Stage 2: pass — r1 fixes in; closing check next
- 2026-11-15 Stage 2: pass — r2 medium bugs fixed; review r2 PASS
- 2026-11-15 Stage 3: pass — review r2 PASS; Learn: two recurring defects filed

## Deviations
- 2026-11-15 .claude-plugin/marketplace.json What: version 0.12.1 -> 0.13.0. Why: the marketplace entry restates the plugin version. Effect: release metadata only
- 2026-11-15 verify_run.py answers, save_output What: two module functions, the reference health probe and the fail-output writer. Why: AC-001, AC-002. Effect: internal to the script
- 2026-11-15 verify_report.py plan, hidden_criteria What: the --plan mode and its reader of hidden manifest entries. Why: AC-004 (plan is the surface named as command verify_report.py --plan). Effect: --plan writes nothing
- 2026-11-15 agents/reference-seeder.md What: example line says one recorder per feature in the plan. Why: it restated the per-module rule this change alters. Effect: docs only
- 2026-11-15 verify_report.py opt What: the option reader moved to module level and rejects an option with no value. Why: review CR-10. Effect: internal
- 2026-11-15 scripts/progress.py What: verify_pending counts criteria in verify scope with no run and no outcome, not modules with any line. Why: review R2-4, recorders go per feature and stop part way. Effect: test_verify_step_sits_between_audit_and_handoff updated to the per-criterion rule; this edit came before its test change, so it was not seen red first
- 2026-11-15 verify_run.py test_hash What: the test-file hash with CRLF read as LF, copied in verify_report.status. Why: review R2-3. Effect: internal

## Open questions
-
