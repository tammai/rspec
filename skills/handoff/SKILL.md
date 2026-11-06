---
name: handoff
description: >
  This skill should be used when the user runs /rspec:handoff or asks to get the
  reverse spec ready to build, plan the build, or hand the spec to a coding agent.
  Gets the ADRs approved, picks the build engine (sdlc or Claude Code), writes
  <spec>/build-plan.md in dependency order and adds a build section to CLAUDE.md.
metadata:
  version: "0.9.4"
---

# /rspec:handoff

Requires stage `tech`. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py . --build-order` first; on resume, do only what `pending` lists; `build-plan` pending at this point while a plan exists means the engine is sdlc and a slice not yet started has more than 10 criteria (e.g. the engine changed after the plan was cut): keep the slices already mapped in `build.slices` as they are, re-cut the rest after them, and number on (`adr-approval`, `build-engine`, `build-plan`, `cutover-plan`, `claude-md`; with `production`, also write the readiness checklist if missing).

## 1. ADR approval gate
- List every ADR in `<decisions>/` with status `Proposed`: title, the recommended decision in one line, and the main alternative.
- Ask the user to accept, change or reject each (one AskUserQuestion round, up to 4 per round). Update each ADR's `Status` to `Accepted` or `Rejected`, and its Decision section if they changed it.
- Once the ADRs are decided, re-read `<spec>/nfr.md` against the accepted ones and update any NFR an accepted decision rules out (say from which release it applies, or drop it with a reason); under autopilot, log each change.
- Once the ADRs are decided, write the stack from the accepted stack ADR into `<spec>/rspec.json` → `stack` (one line, e.g. "Next.js 15 + TypeScript, SQLite, Vitest") and keep `deploy` in step with it, so sdlc setup and the build use the same stack.
- Do not continue while any ADR is `Proposed`. Never accept one on the user's behalf. If `autopilot.enabled` is true in `rspec.json`, do not ask: apply the user's rule in `autopilot.rules` (see the Autopilot section of the pipeline skill), record the decision in `<spec>/autopilot-log.md`, and park anything the rule does not cover. With rule `park`, stop here.

## 2. Build engine
Ask once (AskUserQuestion; under autopilot use `autopilot.rules.build_engine`) how the rebuild will be built, and record it in `<spec>/rspec.json` as `"build": {"engine": "<sdlc|claude-code|none>", "slices": {}}`:
- **sdlc** (offer first, as recommended, when the `sdlc:start` command or `sdlc:orchestrator` skill is available in this session): sdlc defines, builds, reviews and ships each slice; `/rspec:pipeline` drives it slice by slice.
- **claude-code**: build directly from the plan, tracking `status` in the story files.
- **none**: no build is started; still write the plan and the CLAUDE.md section, so whoever builds later has them.

If the choice is sdlc and `.sdlc/config.json` is missing, run `/sdlc:setup` now with the Skill tool (`sdlc:setup`); under autopilot, skip this and leave it to the build stage, which pauses for it. Tell it to use the stack in `rspec.json` → `stack` (the accepted ADR's choice) and the deployment target in `deploy` (sdlc setup asks where it deploys), and that the repo holds a reverse-engineered SRS in `<spec>/` (not code), that the PRD should be drafted from `<spec>/README.md` (goals, scope), `<spec>/features.md` (MVP capabilities, Drop rows as non-goals) and `<spec>/nfr.md` (constraints), and that the API contract is `<contracts>/openapi.json` (in a monorepo: `packages/api-contract/v1/openapi.json`, so the contract check's spec file is `openapi.json`). Follow setup through its own questions, then continue here.

If sdlc is not available but the user wants it, say how to install it and record `claude-code` until they do.

## 3. Build plan
Write `<spec>/build-plan.md` from `${CLAUDE_PLUGIN_ROOT}/templates/build-plan.md`:
- Take `order` from the progress output: every feature in scope, MVP first, dependencies first. Keep that order.
- Group into releases: `## Release 1: MVP` holds every MVP feature; the Later features follow in releases 2 and up, each a coherent increment a user would notice (e.g. "Planning: cycles and projects"). Group a release around one area or module where the dependencies allow, rather than following `order` blindly across modules; a feature still never comes before one it depends on. A release heading and its one-line goal name no feature IDs.
- Group consecutive features into vertical slices by a criteria budget: without sdlc, about 30 acceptance criteria per slice (one build session can finish and test it); with sdlc, as many as needed so that no slice has more than 10 acceptance criteria (sdlc takes about 10 per change), and a story with more than 10 is a slice of its own, each ending in something a user can try (e.g. "sign in and create a workspace", "create and list issues"). The first slice is the thinnest end-to-end path.
- For each feature list its story file, the `operationId`s and schemas whose `x-features` include it, and the NFRs that name it or `all`.
- State the "done when" rule for each slice: every acceptance criterion of its stories has a passing test.

## 4. Cutover plan (modernize track only)
Write `<spec>/cutover-plan.md` from `${CLAUDE_PLUGIN_ROOT}/templates/cutover-plan.md` for the chosen `strategy`:
- rewrite: one cutover after the last slice; the build plan's slices build the new system to parity.
- strangler: one cutover step per slice; order slices so each can be routed to the new system on its own.
- refactor: one step per slice inside the existing codebase, each behind a flag.
The Rollback section is required: trigger, steps, and the point of no return. Data steps follow `<spec>/data-migration.md`.

## 5. Production readiness (when `goal` is `production`, which the modernize track defaults to)
Write `<spec>/production-readiness.md` from `${CLAUDE_PLUGIN_ROOT}/templates/production-readiness.md`:
- Keep every category; keep the Cutover category only in the modernize track (delete it for rspec). Tailor items to this product: name the real SLO targets from the NFRs, the regulations that apply to its users, the roles and tenant boundaries to test.
- Mark an item that cannot apply as checked with `(n/a: <reason>)`, e.g. no personal data stored. Never mark anything else done here; the build proves the rest.
- Tell the user the pipeline will hand the open items to the build after the last slice.

## 6. CLAUDE.md section
- Fill `${CLAUDE_PLUGIN_ROOT}/templates/claude-md-sdlc.md` when the engine is sdlc, else `${CLAUDE_PLUGIN_ROOT}/templates/claude-md.md` (working name, the absolute plugin root path, and `<spec>`, `<contracts>`, `<decisions>`, `<changelog>` from `paths` in the progress output) and add it to `CLAUDE.md` at the project root. Create the file if missing.
- If a `<!-- rspec:handoff -->` … `<!-- /rspec:handoff -->` block already exists, replace only that block. Never change anything else in CLAUDE.md.

Features triaged into or out of scope after handoff are added to or removed from this plan by `rspec:features` Triage, not by rewriting it.

## 7. Finish
- Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .` with stage set to `handoff`; fix errors.
- Set `stage` to `handoff`, add a line to `<changelog>`.
- Reply with: the slices (name and feature count), the accepted decisions, and how to start: with sdlc, "`/rspec:pipeline continue` hands slice 1 to sdlc"; with claude-code, "ask Claude to build slice 1 from <spec>/build-plan.md".
