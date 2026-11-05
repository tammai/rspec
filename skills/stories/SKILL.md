---
name: stories
description: >
  This skill should be used when the user runs /rspec:stories or asks to write user
  stories, acceptance criteria or detailed feature specs for the approved MVP of the
  product being reverse-specced. Runs one story-writer subagent per module in parallel.
argument-hint: "[module codes, optional; default all with MVP features]"
metadata:
  version: "0.3.0"
---

# /rspec:stories

Requires stage `features-approved` or later. If the stage is `discovered`, stop and ask the user to approve features first.

1. Read `<spec>/features.md`; group MVP rows by module code. If `$ARGUMENTS` lists module codes, restrict to those. Include Later features only if the user asks. On resume, give each subagent only its pending MVP IDs.
2. Launch one `rspec:story-writer` subagent per module that has MVP features, **all in a single message** (batches of 8 if more). Give each: `track`, product, `lang`, module code and name, its MVP rows verbatim, the path of its research file, IDs of MVP features in other modules it may depend on, and the absolute path of `${CLAUDE_PLUGIN_ROOT}`.
3. After all return, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .` and fix any errors (missing stories, empty criteria, leftover placeholders). Re-run a subagent for a module only if most of its files are broken.
4. The check script already rejects unknown or non-MVP dependencies and cycles. Fix those in the story frontmatter, not in features.md, unless the user agrees to change a priority.
5. Set `stage` to `stories`, add a line to `<changelog>`, and reply with: stories written per module, any features whose acceptance criteria rest mostly on `[inferred]` facts, and next step `/rspec:tech`.
