# Part plan: 2026-11-08-l-rspec-criteria-ids B1

**Record:** the feature's change file (`scaffold.py paths <feature>` → `change`) · **Backlog:** [backlog.md](backlog.md)

## Tasks

1. **Vendor contracts v1** — AC-001
   - Files: `contracts/v1/`, `.gitattributes`, `tests/test_contracts_vendor.py`
   - Test first: vendor-check on `contracts/v1` (red with the folder absent)
   - Then: byte-identical copy from product-rebuild `34dd29a`, `contracts/v1/** -text`
2. **Story template and writers on C1/C2** — AC-003
   - Files: `templates/feature-story.md`, `agents/story-writer.md`, `skills/stories/SKILL.md`, `agents/consistency-auditor.md`, `templates/claude-md.md`, `references/writing-rules.md`
   - Test first: template passes `contracts.check_story` structurally, has `.AC1` IDs and `## Open questions`
   - Then: IDs, Failure modes, Must never break, Open questions; Edge cases removed; citations under Sources
3. **check_spec on contracts** — AC-002
   - Files: `scripts/check_spec.py`, `tests/helpers.py`, `tests/test_criteria_ids.py`
   - Test first: legacy, no-example-data, no-tag and no-ID stories fail naming the file
   - Then: `story_issues` (check_story + check_criteria with domain.md; TODO and Differences as WARN)
4. **migrate_criteria.py** — AC-004
   - Files: `scripts/migrate_criteria.py`
   - Test first: IDs AC3/AC2/AC4 in file order, Edge cases → `→ TODO`, second run byte-identical
   - Then: the script
5. **Criteria lock** — AC-005
   - Files: `scripts/check_spec.py`, `CHANGELOG.md`, `README.md`
   - Test first: lock valid under check_lock; changed text → level 0 and `needs re-verify`; failing check writes none
   - Then: `write_lock`

## Public Surface

- command `scripts/migrate_criteria.py` — AC-004
- dependency `contracts/v1` (vendored) — AC-001
