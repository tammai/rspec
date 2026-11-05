---
name: handoff
description: >
  This skill should be used when the user runs /rspec:handoff or asks to get the
  reverse spec ready to build, plan the build, or hand the spec to a coding agent.
  Gets the ADRs approved, picks the build engine (sdlc or Claude Code), writes
  <spec>/build-plan.md in dependency order and adds a build section to CLAUDE.md.
metadata:
  version: "0.5.0"
---

# /rspec:handoff

Requires stage `tech`. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py . --build-order` first; on resume, do only what `pending` lists (`adr-approval`, `build-engine`, `build-plan`, `claude-md`).

## 1. ADR approval gate
- List every ADR in `<decisions>/` with status `Proposed`: title, the recommended decision in one line, and the main alternative.
- Ask the user to accept, change or reject each (one AskUserQuestion round, up to 4 per round). Update each ADR's `Status` to `Accepted` or `Rejected`, and its Decision section if they changed it.
- Do not continue while any ADR is `Proposed`. Never accept one on the user's behalf.

## 2. Build engine
Ask once (AskUserQuestion) how the rebuild will be built, and record it in `<spec>/rspec.json` as `"build": {"engine": "<sdlc|claude-code|none>", "slices": {}}`:
- **sdlc** (offer first, as recommended, when the `sdlc:start` command or `sdlc:orchestrator` skill is available in this session): sdlc defines, builds, reviews and ships each slice; `/rspec:pipeline` drives it slice by slice.
- **claude-code**: build directly from the plan, tracking `status` in the story files.
- **none**: stop after the plan.

If the choice is sdlc and `.sdlc/config.json` is missing, run `/sdlc:setup` now with the Skill tool (`sdlc:setup`). Tell it that the repo holds a reverse-engineered SRS in `<spec>/` (not code), that the PRD should be drafted from `<spec>/README.md` (goals, scope), `<spec>/features.md` (MVP capabilities, Drop rows as non-goals) and `<spec>/nfr.md` (constraints), and that the API contract is `<contracts>/openapi.json` (in a monorepo: `packages/api-contract/v1/openapi.json`, so the contract check's spec file is `openapi.json`). Follow setup through its own questions, then continue here.

If sdlc is not available but the user wants it, say how to install it and record `claude-code` until they do.

## 3. Build plan
Write `<spec>/build-plan.md` from `${CLAUDE_PLUGIN_ROOT}/templates/build-plan.md`:
- Take `order` from the progress output: every MVP feature, dependencies first. Keep that order.
- Group consecutive features into 3–8 vertical slices (with sdlc: at most about 10 acceptance criteria per slice, since sdlc takes about 10 per change; split a bigger slice), each ending in something a user can try (e.g. "sign in and create a workspace", "create and list issues"). The first slice is the thinnest end-to-end path.
- For each feature list its story file, the `operationId`s and schemas whose `x-features` include it, and the NFRs that name it or `all`.
- State the "done when" rule for each slice: every acceptance criterion of its stories has a passing test.

## 4. CLAUDE.md section
- Fill `${CLAUDE_PLUGIN_ROOT}/templates/claude-md-sdlc.md` when the engine is sdlc, else `${CLAUDE_PLUGIN_ROOT}/templates/claude-md.md` (working name, the absolute plugin root path, and `<spec>`, `<contracts>`, `<decisions>`, `<changelog>` from `paths` in the progress output) and add it to `CLAUDE.md` at the project root. Create the file if missing.
- If a `<!-- rspec:handoff -->` … `<!-- /rspec:handoff -->` block already exists, replace only that block. Never change anything else in CLAUDE.md.

## 5. Finish
- Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .` with stage set to `handoff`; fix errors.
- Set `stage` to `handoff`, add a line to `<changelog>`.
- Reply with: the slices (name and feature count), the accepted decisions, and how to start: with sdlc, "`/rspec:pipeline continue` hands slice 1 to sdlc"; with claude-code, "ask Claude to build slice 1 from <spec>/build-plan.md".
