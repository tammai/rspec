---
name: handoff
description: >
  This skill should be used when the user runs /rspec:handoff or asks to get the
  reverse spec ready to build, plan the build, or hand the spec to a coding agent.
  Gets the ADRs approved, writes docs/build-plan.md in dependency order and adds a
  build section to the project's CLAUDE.md.
metadata:
  version: "0.3.0"
---

# /rspec:handoff

Requires stage `tech`. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py . --build-order` first; on resume, do only what `pending` lists (`adr-approval`, `build-plan`, `claude-md`).

## 1. ADR approval gate
- List every ADR in `docs/decisions/` with status `Proposed`: title, the recommended decision in one line, and the main alternative.
- Ask the user to accept, change or reject each (one AskUserQuestion round, up to 4 per round). Update each ADR's `Status` to `Accepted` or `Rejected`, and its Decision section if they changed it.
- Do not continue while any ADR is `Proposed`. Never accept one on the user's behalf.

## 2. Build plan
Write `docs/build-plan.md` from `${CLAUDE_PLUGIN_ROOT}/templates/build-plan.md`:
- Take `order` from the progress output: every MVP feature, dependencies first. Keep that order.
- Group consecutive features into 3–8 vertical slices, each ending in something a user can try (e.g. "sign in and create a workspace", "create and list issues"). The first slice is the thinnest end-to-end path.
- For each feature list its story file, the `operationId`s and schemas whose `x-features` include it, and the NFRs that name it or `all`.
- State the "done when" rule for each slice: every acceptance criterion of its stories has a passing test.

## 3. CLAUDE.md section
- Fill `${CLAUDE_PLUGIN_ROOT}/templates/claude-md.md` (working name, the absolute plugin root path) and add it to `CLAUDE.md` at the project root. Create the file if missing.
- If a `<!-- rspec:handoff -->` … `<!-- /rspec:handoff -->` block already exists, replace only that block. Never change anything else in CLAUDE.md.

## 4. Finish
- Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .` with stage set to `handoff`; fix errors.
- Set `stage` to `handoff`, add a CHANGELOG line.
- Reply with: the slices (name and feature count), the accepted decisions, and how to start: "open a session in this repo and ask Claude to build slice 1 from docs/build-plan.md".
