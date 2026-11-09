# Part plan: 2026-11-08-l-rspec-criteria-ids B5

**Record:** the feature's change file (`scaffold.py paths <feature>` → `change`) · **Backlog:** [backlog.md](backlog.md)

## Tasks

1. **amend.py** — AC-011, AC-016, AC-017
   - Files: `scripts/amend.py`, `scripts/verify_report.py`, `tests/test_amend.py`
   - Test first: edit at level 2 → new text, changelog line, level 0, `verify --only` named; bad text refused with nothing written; `--new` takes the next unused number past a struck one; spec-gap finding applied, build-defect and unreproduced refused; `--test` removes the recorded test and its old runs no longer count
   - Then: the script; `verify_report.status` ignores runs of a removed test
2. **Skill and routing** — AC-011 (prose)
   - Files: `skills/amend/SKILL.md`, `skills/verify/SKILL.md`, `skills/pipeline/SKILL.md`, `README.md`, `CHANGELOG.md`
   - Then: /rspec:amend; verify's spec-wrong and test-wrong go through amend; the pipeline answers sdlc spec questions with `--finding`

## Public Surface

- command `scripts/amend.py` — AC-011
