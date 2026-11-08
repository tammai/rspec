# Part plan: 2026-11-08-l-rspec-criteria-ids B2

**Record:** the feature's change file (`scaffold.py paths <feature>` → `change`) · **Backlog:** [backlog.md](backlog.md)

## Tasks

1. **R8 departures registry** — AC-007
   - Files: `scripts/check_spec.py`, `skills/features/SKILL.md`, `skills/stories/SKILL.md`, `agents/story-writer.md`, `tests/test_departures.py`
   - Test first: Differences without a link, a dangling link and an undecided entry fail; an accepted entry passes and reaches the lock; a proposed entry warns before handoff and errors at handoff
   - Then: `check_departures` (contracts C5 + dangling scan of stories and features.md), lock `departures` from the registry; features approval writes entries; writers link them
2. **R3 PRD** — AC-006 (manual: skill prose)
   - Files: `skills/handoff/SKILL.md`
   - Then: step 2a writes `<docs>/prd.md` (sdlc docs_dir, else docs/sdlc) with sdlc's PRD sections, each a paragraph plus SRS links; setup told to use it as is; the draft-from-rspec instruction deleted
3. **R6 templates** — AC-008
   - Files: `templates/build-plan.md`, `templates/claude-md-sdlc.md`, `templates/claude-md.md`, `skills/handoff/SKILL.md`, `skills/pipeline/SKILL.md`, `scripts/check_spec.py`, `tests/test_build_plan_criteria.py`
   - Test first: a slice that leaves out a criterion ID warns; templates carry the bundle path, level-2 done rule and read-only rule
   - Then: Criteria column, bundle line, done-when rule; cite-only and read-only rules; run-http / playwright commands in the Claude Code variant

## Public Surface

- none (no new command; `departures.yaml` is a contracts C5 file)

## Open

- Q5 (with the user): how a story writer records a difference that has no accepted entry yet.
