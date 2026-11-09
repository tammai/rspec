# 2026-11-09-m-rules-recall
Status: done
Process: 3
Change: docs/sdlc/changes/2026-11-09-m-rules-recall.md   (this feature's record for people)
Track: M   (sized up because: —; footprint: 20 files)
Risk: low
Top model: opus   (fable only if the user chose it)
Commands: test: `python -m unittest discover tests`
Started: 2026-11-09
Base: 1a84c76
Owner: tammai.it@gmail.com
Tool: claude-code
Verified: 1a84c76 tree e714f46e3721af5402f6054f5d634c84c69fcfe7
Current: Stage 4 – Ship

## Stages
- [x] 1 Define   — the change file, the plan sections below
- [x] 2 Build
- [x] 3 Review   — the change file's ## Review
- [ ] 4 Ship     — PR: (Learn: knowledge, recurring-defects.md)

## How the build runs
inline, this session

## Handoff
- Real OSS runs (bigin-phish-rspec) cite ranges and comma lists (route.go:395-403; ratelimit.go:13-15, 130-143) and file-level paths in domain.md
- contracts.parse_yaml reads gold.yaml (flow maps and nested lists) — stdlib only
- Another state file (2026-11-08-l-rspec-criteria-ids) still says active though shipped as v0.11.0; pass --feature explicitly

## Tasks
1. **Scorer** — AC-001 AC-002 AC-003 AC-004 AC-005
   - Files: `scripts/rules_recall.py`
2. **Test** — AC-001 AC-002 AC-003 AC-004 AC-005
   - Files: `tests/test_rules_recall.py`
3. **Fixture** — AC-006
   - Files: `tests/fixtures/rules-recall/README.md`, `tests/fixtures/rules-recall/gold.yaml`, `tests/fixtures/rules-recall/reference-src/app/controllers/invoices_controller.rb`, `tests/fixtures/rules-recall/reference-src/app/jobs/dunning_job.rb`, `tests/fixtures/rules-recall/reference-src/app/models/invoice.rb`, `tests/fixtures/rules-recall/reference-src/app/models/line_item.rb`, `tests/fixtures/rules-recall/reference-src/app/policies/invoice_policy.rb`, `tests/fixtures/rules-recall/reference-src/app/services/invoice_issuer.rb`, `tests/fixtures/rules-recall/reference-src/app/services/late_fee_calculator.rb`, `tests/fixtures/rules-recall/reference-src/app/services/payment_recorder.rb`, `tests/fixtures/rules-recall/reference-src/config/billing.rb`
4. **Release 0.11.1** — AC-007
   - Files: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `CHANGELOG.md`, `README.md`

## Public Surface
- command `rules_recall.py <project-or-spec> [--model <tier>]` — AC-001

## Gate log
- 2026-11-09 Stage 1: pass — plan not stopped for approval: low-risk M
- 2026-11-09 Stage 2: pass
- 2026-11-09 review: ran code (Public Surface is not none), not asked: low risk
- 2026-11-09 Stage 2: pass
- 2026-11-09 user decision (Tam Mai, via coordinator msg_3b4da7960132, after round 2 FAIL): fix round, redesign scripts/rules_recall.py to stop guessing; one round-3 closing check, no round 4; a new high at round 3 stops with the branch unpushed
- 2026-11-09 Stage 2: pass
- 2026-11-09 Stage 2: pass
- 2026-11-09 Stage 3: pass

## Deviations
- 2026-11-09 tests/test_rules_recall.py What: Run command changed from 'python -m unittest tests.test_rules_recall' to 'python -m unittest discover tests -p test_rules_recall.py'. Why: the tests import helpers flat, so the first red step failed on the import, not the missing script. Effect: red re-recorded with the script absent (fails on 'can't open file').
- 2026-11-09 scripts/rules_recall.py What: top-level functions citations, claims, located, missing_values, own_text, pct and main are reported as exports. Why: the script is a CLI (the declared command surface); like every script in scripts/, its functions are internal and nothing imports them. Effect: no public surface beyond the command.
- 2026-11-09 scripts/rules_recall.py What: review round 1 fixes add internal functions normal and has_value. Why: one normalisation for every citation form (F5, F6) and number-bounded value matching (F1). Effect: still no public surface beyond the command.
- 2026-11-09 scripts/rules_recall.py What: citation = exact token path:N or path:N-M (no spaces, start <= end; reversed, spaced, en-dash, comma-list continuation, backslash and #L forms are not citations); a numeric value matches a whole number token by value with % part of it, after removing every ABC-12 style ID. Why: user decision after review round 2 (R1 high, R2-R6). Effect: Decisions row 'Ranges' narrowed: a range counts when it overlaps a location, only in the exact-token form; comma lists, #L anchors and backslash paths become tickets.
- 2026-11-09 scripts/rules_recall.py What: the redesign adds the internal function number and removes normal. Why: numeric values compared by value (user decision after round 2). Effect: no public surface beyond the command.

## Open questions
-
