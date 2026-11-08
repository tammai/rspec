---
name: stories
description: >
  This skill should be used when the user runs /rspec:stories or asks to write user
  stories, acceptance criteria or detailed feature specs for the approved features of the
  product being reverse-specced. Runs one story-writer subagent per module in parallel.
argument-hint: "[module codes, optional; default all modules in scope]"
metadata:
  version: "0.9.6"
---

# /rspec:stories

Requires stage `features-approved` or later. If the stage is `discovered`, stop and ask the user to approve features first.

1. Read `<spec>/features.md` and `scope` in `rspec.json`. The features in scope are the MVP rows, plus the Later rows when `scope` is `full` (the default); never Drop rows. Group them by module code. Put the modules in dependency order, foundations first (e.g. accounts and workspaces before issues, issues before notifications and views); a feature's `depends_on` names only its own module or modules earlier in that order, so parallel writers cannot create cycles between modules; a real need on a later module goes in `also_needs` and is merged after the last round (step 3). If `$ARGUMENTS` lists module codes, restrict to those. On resume, use `pending` from the progress output (MVP first, then Later).
2. Split each module's features into batches of about 10, MVP first. Write in rounds: each round launches one `rspec:story-writer` per module that still has a batch, **all in a single message** (8 at a time if more), so every MVP story is written before any Later one. Give each writer: `track`, product, `lang`, module code and name, its batch's rows verbatim (with priority), the path of its research file, the IDs it may depend on (the features of earlier batches of its own module and of the modules **earlier** in the dependency order, each with its priority), the path of `<spec>/domain.md`, and the absolute path of `${CLAUDE_PLUGIN_ROOT}`.
3. After the last round, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/merge_deps.py .`: it moves each `also_needs` into `depends_on` unless it would close a cycle or make an MVP feature need a Later one, and lists what it skipped; a skipped need is a real ordering problem, never dropped silently: split or move one of the two features, or ask the user (autopilot: park it under `## Parked` with both IDs). Then read every story's `## Open questions`, Failure modes and Differences against `domain.md` and against the other stories: add each new shared rule to `domain.md` once, and make the stories that disagree with it agree (or park the conflict); then empty each story's `## Open questions` to `- none`. After all rounds, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .` and fix any errors (missing stories, criteria breaking contracts C1, missing story sections, leftover placeholders). A spec written before 0.11 first needs `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/migrate_criteria.py .`; each `→ TODO` failure mode it leaves is a warning naming the module to re-run here. Re-run a subagent for a module only if most of its files are broken.
4. The check script already rejects unknown dependencies, an MVP feature depending on a Later one, and cycles. Fix those in the story frontmatter, not in features.md, unless the user agrees to change a priority.
5. Set `stage` to `stories` (never move a later stage back), add a line to `<changelog>`, and reply with: stories written per module, any features whose acceptance criteria rest mostly on `[inferred]` facts, and next step `/rspec:tech`.
