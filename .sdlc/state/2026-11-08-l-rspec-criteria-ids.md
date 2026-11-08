# 2026-11-08-l-rspec-criteria-ids
Status: active
Process: 3
Change: docs/sdlc/changes/2026-11-08-l-rspec-criteria-ids.md   (this feature's record for people)
Track: L   (sized up because: written spec sized L with 5 backlog parts (rebuild-upgrade README); footprint: 12 files)
Risk: low
Top model: opus   (fable only if the user chose it)
Commands: test: `python -m unittest discover tests`
Started: 2026-11-08
Base: 0bef83f
Owner: tammai.it@gmail.com
Tool: claude-code
Verified: 0bef83f tree 9a483ab10611ac1069fb5c4111baf4514f63c759
Slice: B2   Slice base: 1e50121   Slice gates: none
Current: Stage 2 – Build

## Stages
- [x] 1 Define   — the change file, the plan sections below
- [ ] 2 Build
- [ ] 3 Review   — the change file's ## Review
- [ ] 4 Ship     — PR: (Learn: knowledge, recurring-defects.md)

## How the build runs
parts in fresh sessions: each spec part is its own orchestrator task; this session builds B1 only

## Handoff
- contracts API used: contracts.check_story, check_criteria(profile='rspec', domain=...), criterion_text_sha256, check_lock (contracts/v1/contracts.py)
- Q1/Q3 answered (a)/(a): severities live in `story_issues` (scripts/check_spec.py); `## Open questions` section in templates/feature-story.md and agents/story-writer.md
- B1 done. For B2 (R8): `story_issues` downgrades "difference must end with → D-" to a WARN; make it an ERROR and add the dangling D- check; `write_lock` keeps `departures: []` (scripts/check_spec.py), fill it from the Differences links
- Smoke run on bigin-phish-rspec (scratch copy): migration 111 stories, idempotent; check then shows 679 errors, 557 of them grammar because criteria carry a `[code]` citation after the tag (`repo@… path:line`). story-writer and writing-rules now put citations under Sources; legacy specs need a stories pass

## Tasks
1. **B1 Vendor contracts v1 + drift test** — AC-001
   - Files: `contracts/v1/`, `.gitattributes`, `tests/test_contracts_vendor.py`
2. **B1 Story template, story-writer, stories skill, auditors** — AC-003
   - Files: `templates/feature-story.md`, `agents/story-writer.md`, `skills/stories/SKILL.md`, `agents/consistency-auditor.md`, `templates/claude-md.md`, `references/writing-rules.md`
3. **B1 check_spec C1/C2 via contracts** — AC-002
   - Files: `scripts/check_spec.py`, `scripts/rspec_lib.py`, `tests/helpers.py`, `tests/test_criteria_ids.py`
4. **B1 migrate_criteria.py** — AC-004
   - Files: `scripts/migrate_criteria.py`
5. **B1 criteria lock** — AC-005
   - Files: `scripts/check_spec.py`, `CHANGELOG.md`, `README.md`
6. **B2 PRD, departures, handoff templates** — AC-006 AC-007 AC-008
   - Files: `skills/handoff/SKILL.md`, `skills/features/SKILL.md`, `templates/`
7. **B3 per-tag audit sampling** — AC-009
   - Files: `scripts/audit_sample.py`, `agents/fact-checker.md`
8. **B4 verify stage** — AC-010
   - Files: `skills/verify/`, `agents/`, `scripts/progress.py`, `tests/fixtures/reference-app/`
9. **B5 amend** — AC-011
   - Files: `skills/amend/`

## Public Surface
- command `scripts/migrate_criteria.py` — AC-004
- dependency `contracts/v1 (vendored)` — AC-001

## Gate log
- 2026-11-08 Stage 1: pass — plan self-approved (L), partial: (1) spec R1/R2 + 01 vendoring map to AC-001..005, R3-R8 indexed as AC-006..011 for later parts; (2) open questions Q1/Q3 are with the user via orchestrator, built in one place each; (3) Q2/Q4 settled by orchestrator msg_ae7b769d541a; (4) nothing irreversible

## Deviations
- 2026-11-08 Vendored contracts/v1/ (task 1 names the folder; verify lists each file and function): contracts/v1/MANIFEST contracts/v1/acceptance-manifest.schema.json contracts/v1/contracts.py contracts/v1/cost-line.schema.json contracts/v1/criteria-lock.schema.json contracts/v1/departures.schema.json contracts/v1/finding.schema.json contracts/v1/fixtures/bundle/invalid/seed-outside-bundle/http/F-ISS-01.AC2.yaml contracts/v1/fixtures/bundle/invalid/seed-outside-bundle/manifest.json contracts/v1/fixtures/bundle/invalid/seed-outside-bundle/seed/team-eng-11-issues.yaml contracts/v1/fixtures/bundle/invalid/sha256-mismatch/http/F-ISS-01.AC2.yaml contracts/v1/fixtures/bundle/invalid/sha256-mismatch/manifest.json contracts/v1/fixtures/bundle/invalid/sha256-mismatch/seed/team-eng-11-issues.yaml contracts/v1/fixtures/bundle/invalid/url-in-test/http/F-ISS-01.AC2.yaml contracts/v1/fixtures/bundle/invalid/url-in-test/manifest.json contracts/v1/fixtures/bundle/invalid/url-in-test/seed/team-eng-11-issues.yaml contracts/v1/fixtures/bundle/valid/trackr/http/F-ISS-01.AC2.yaml contracts/v1/fixtures/bundle/valid/trackr/manifest.json contracts/v1/fixtures/bundle/valid/trackr/seed/team-eng-11-issues.yaml contracts/v1/fixtures/cost/invalid/negative-wall-s.jsonl contracts/v1/fixtures/cost/valid/cost.jsonl contracts/v1/fixtures/departures/invalid/no-decided-by.yaml contracts/v1/fixtures/departures/invalid/proposed-blocks.yaml contracts/v1/fixtures/departures/valid/departures.yaml contracts/v1/fixtures/finding/invalid/no-verified-by.json contracts/v1/fixtures/finding/invalid/route-mismatch.json contracts/v1/fixtures/finding/valid/BH-0007.json contracts/v1/fixtures/finding/valid/BH-0008-not-reproduced.json contracts/v1/fixtures/http/invalid/capture-used-before-taken.yaml contracts/v1/fixtures/http/invalid/json-not-a-list.yaml contracts/v1/fixtures/http/invalid/no-steps.yaml contracts/v1/fixtures/http/valid/F-ISS-01.AC2.yaml contracts/v1/fixtures/lock/invalid/level-2-without-test.json contracts/v1/fixtures/lock/invalid/tag-with-brackets.json contracts/v1/fixtures/lock/valid/trackr/criteria.lock.json contracts/v1/fixtures/yaml/invalid/anchor.yaml contracts/v1/fixtures/yaml/invalid/block-scalar.yaml contracts/v1/fixtures/yaml/invalid/duplicate-key.yaml contracts/v1/fixtures/yaml/invalid/empty-key.yaml contracts/v1/fixtures/yaml/invalid/unclosed-flow-value.yaml contracts/v1/fixtures/yaml/valid/scalars.yaml contracts/v1/test_contracts.py SchemaUnsupported YamlError check_bundle check_cost check_criteria check_departures check_finding check_http_test check_id check_lock check_story criterion_text_sha256 finding_route header_for parse_yaml run_fixtures run_http schema_errors seal sum_cost vendor_check  What: copied byte-identical from product-rebuild 34dd29a. Why: 01 Distribution; never edited here. Effect: vendor-check passes; no rspec code beyond check_spec imports it.
- 2026-11-08 tests/test_check_spec.py tests/test_quality_bar.py tests/test_scorecard.py What: adapted to the C1/C2 story format (failure= instead of edge=; untagged criterion now an ERROR, not a WARN). Why: helpers.story() changed format and the evidence-tag warning became contracts' source-tag error. Effect: same behaviours asserted, stricter where the rule is now an error.
- 2026-11-08 New module-level helpers body_end find main migrate sections (scripts/migrate_criteria.py) story_issues write_lock (scripts/check_spec.py) What: internal functions of the planned scripts. Why: verify lists new functions as surface. Effect: none outside the scripts; the only new command is migrate_criteria.py (Public Surface).
- 2026-11-08 New helpers criterion_ids and check_departures in scripts/check_spec.py, and tests/test_departures.py tests/test_build_plan_criteria.py skills/pipeline/SKILL.md (B2) What: internal functions, the part's tests, and the pipeline's slice request now cites criterion IDs. Why: verify lists new functions; the pipeline request restated the old cite-the-story rule R6 replaces. Effect: none outside check_spec; pipeline asks sdlc for '- **AC-001** -> F-ISS-01.AC2' ACs.

## Open questions
-
