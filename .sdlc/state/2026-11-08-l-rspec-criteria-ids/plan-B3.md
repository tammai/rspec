# Part plan: 2026-11-08-l-rspec-criteria-ids B3

**Record:** the feature's change file (`scaffold.py paths <feature>` → `change`) · **Backlog:** [backlog.md](backlog.md)

## Tasks

1. **Per-tag sampling and level 1** — AC-009
   - Files: `scripts/audit_sample.py`, `scripts/check_spec.py`, `tests/test_audit.py`
   - Test first: sample sizes per tag (40→8, 3→3, 200→25, 26→6, 12→5, `[3p]` not sampled), same on rerun; verdicts → level 1 for sampled-confirmed and clean populations, 0 for findings and for a contradicted population's unsampled members, 0 again after a text change
   - Then: `draw` writes sample.md + sample.json; `--levels` reads facts.md's Verdict column and writes audit/levels.json (ID → text hash); `write_lock` raises 0 → 1 while the hash matches
2. **Fact-checker and audit skill** — AC-009 (prose)
   - Files: `agents/fact-checker.md`, `skills/audit/SKILL.md`, `README.md`, `CHANGELOG.md`
   - Then: per-tag checking (`[code]` at the pinned commit, `[observed]` read-only via Playwright or the research note, `[inferred]` contradiction + decision), exact verdict words and table header, DECISION to the user or parked, `--levels` before check

## Public Surface

- command `scripts/audit_sample.py --levels` — AC-009
