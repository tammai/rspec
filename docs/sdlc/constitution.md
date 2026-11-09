# rspec Constitution

Inferred at sdlc setup (2026-11-08) from the repo's scripts, tests, README and RELEASE.md; approved under the
coordinator's "recommended defaults" instruction (gate G-A). Amend through `sdlc:project-constitution`.

## Core Principles

### I. Stdlib-only, no install step
Scripts MUST run on the user's Python 3 with no `pip install`. Vendored code (such as `contracts/v1/`) is copied
byte-identical from its source and verified, never edited in place.

### II. Deterministic checks live in scripts, judgement in agents
A rule that can be checked mechanically MUST be a script (`check_spec.py`, `audit_sample.py`, `progress.py`), not
a sentence in a skill or agent prompt. Figures in reports are computed by scripts, never written by an agent.

### III. Every behaviour change has a test
A change to a script MUST come with a case in `tests/` that fails before the change and passes after. One test
per user-visible behaviour: the happy path plus the failure that matters most.

### IV. No silent pass
A check that cannot run MUST say it did not run, never pass. Validators refuse what they do not understand.

### V. Simplicity
Changes MUST be the smallest that meet the acceptance criteria. New abstractions, options, configuration, public exports and dependencies MUST be justified by a current requirement, not a possible future one; an abstraction with a single implementation needs a written reason. Comments MUST explain *why*, never restate the code or its change history; doc comments are for exported API and are one line unless the contract needs more.

### VI. Existing specs keep working
A change to `rspec.json` fields, stage names or the story format MUST ship a migration path for specs already
written (a script or a documented `/rspec:pipeline continue`), and is a minor bump while 0.x (RELEASE.md).

### VII. Releases are versioned and recorded
Every release sets the same version in `.claude-plugin/plugin.json` and `marketplace.json`, adds a
`CHANGELOG.md` entry, and passes `python -m unittest discover tests` and `claude plugin validate .`.

## Platform constraints

Runs on Windows (Git Bash), macOS and Linux. Paths, line endings and encodings (`utf-8-sig` reads) MUST be
handled for all three.

## Review

Work merges to `main` only after review and with tests no worse than `.sdlc/baseline.md`.

## Governance

This constitution overrides other practice in this repo. Amendments are recorded with a date and a reason.

**Version**: 1.0.0 | **Ratified**: 2026-11-08 | **Last Amended**: 2026-11-08
