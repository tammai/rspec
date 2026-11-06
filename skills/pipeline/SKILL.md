---
name: pipeline
description: >
  This skill should be used when the user runs /rspec:pipeline or asks to run the
  whole reverse spec end to end, or to pause, stop, resume, continue or check the
  status of it, including in a new session ("do the full spec for Linear", "run all
  rspec steps", "continue the spec", "pause the pipeline", "where is the spec at"). Also
  for modernizing your own product ("modernize our legacy app", "rewrite our product
  on a new stack", "migrate our app from X to Y"). Also
  runs unattended ("run the spec on autopilot", "--autopilot").
  Drives init → discover → features → stories → tech → handoff → check, then hands the build to sdlc slice by slice, from where it left off,
  pausing at the features and ADR approval gates.
argument-hint: "[product | continue | pause | stop | status] [--until <stage>]"
metadata:
  version: "0.8.4"
---

# /rspec:pipeline

Drive the reverse spec to a finished, checked spec, across as many sessions as it takes. Each stage is done by its own skill; this skill sequences them, saves a checkpoint and stops when the user asks or something needs them.

## Arguments (`$ARGUMENTS`)

| Argument | Meaning |
|---|---|
| empty or `continue` | Start, or resume from the checkpoint |
| `<product>` | Start a new spec for that product (only if no spec exists); asks for the track |
| `--track rspec\|modernize` | Choose the track up front |
| `pause` | Pause: save the checkpoint, keep the run's settings, end the turn |
| `stop` | Stop: end this run and clear `stop_after`; a later run starts fresh from the saved stage |
| `status` | Report the checkpoint and pending work; change nothing |
| `--autopilot [rules.json]` | Run unattended: ask everything once up front (or read the rules file), then apply the rules at every gate; see Autopilot |
| `--until <stage>` | Stop after that stage (`discover`, `features`, `stories`, `tech`, `handoff`, `build`, `readiness`) |

Plain words count too: "pause", "stop here", "carry on", "resume" in the user's language mean the same as the arguments.

## Where things stand

The truth is on disk. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py .` at the start of every turn of this skill, and after each unit of work. It prints JSON with `stage`, `next` (the step to run), `pending` (what that step still has to do: module codes, MVP feature IDs, tech areas, `module-map`, `screens`, `adrs`, `approval`, `adr-approval`, `build-plan`, `claude-md`, slice numbers for `build`, readiness categories for `readiness`, `check`) and, while building with sdlc, `slices` (each slice's features, its sdlc feature and that feature's sdlc status) and the saved `pipeline` checkpoint.

The checkpoint lives in `<spec>/rspec.json`:

```json
"pipeline": {
  "status": "running | paused | stopped | awaiting-approval | done",
  "stop_after": null,
  "current": "discover",
  "last": "module-explorer finished WS, TEAM, ISS",
  "updated": "<ISO date-time>"
}
```

Write it whenever status changes and after each batch of subagents returns, so a session that ends without warning loses at most one batch.

## Start or resume

1. Run `progress.py`. If there is no spec, ask which track (AskUserQuestion, skip if the request already says):
   - **rspec**: reverse-spec someone else's product, to learn from it, use it personally or run it as a service.
   - **modernize**: move your own product to a new stack (rewrite, strangler fig or refactor in place), with parity, data migration and cutover.
   Then run `rspec:init` with the product and the track (ask for the product if missing).
2. If `pipeline.status` is `running`, the last session ended without pausing. Say so, and treat files written by the last batch as suspect: recheck them (research file has Screens, Features observed and Sources; story passes `check_spec.py`) and redo only the broken ones.
3. If `next` is `done`, the pipeline has finished: say so, report the parked count if any, and stop. Otherwise tell the user in two lines: stage, what is done, what is pending, and the next step.
4. Set `status` to `running`, `current` to the next step, then enter the loop.

## Loop

1. Run the next step's skill with the Skill tool: `rspec:discover`, `rspec:features`, `rspec:stories`, `rspec:tech`, `rspec:handoff` or `rspec:check`. `build` and `readiness` are not skills; they are handled in the sections below. Pass the `pending` list and say it is a resume, so the skill does only the pending units and leaves finished files alone.
2. After each batch of subagents: update `last` and `updated`.
3. When the step's skill finishes: confirm with `progress.py` that the stage advanced, and run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .`. If errors remain after one fix attempt, set `status` to `paused`, show the errors and end the turn.
4. If the user has asked to pause or stop, or the finished stage equals `stop_after`, apply Pause/Stop below. Otherwise continue with the next step.

## Autopilot

Unattended mode, for a product you know well or a second run. Started by `--autopilot`, or by "run it unattended / autopilot" in plain words.

**Before anything runs, collect every answer in one round**, so nothing waits on the user later:
- If a rules file is given (default `rspec-autopilot.json` at the project root, template `${CLAUDE_PLUGIN_ROOT}/templates/autopilot.json`), read it. Otherwise ask with AskUserQuestion, up to 4 questions per call, in as few calls as possible: track, product, goal, focus, stack, layout; for modernize the repos, current stack, drivers and strategy; then the rules below.
- In a headless session (`claude -p`) nothing can be asked: if the rules file is missing or lacks the product or track, stop at once and list what is missing.
- If `build_engine` is `sdlc` and `.sdlc/config.json` is missing at the project root: sdlc setup scaffolds a stack and stops for the user to approve it, so the stack must be decided once, by the user, for both rspec and sdlc. Never run sdlc setup unattended.
  - **`stack` given** (in the rules or the answers): ask the user to run `/sdlc:setup` now with that stack, before the run; in a headless session stop at once with that message. The tech stage then records this stack in its stack ADR instead of choosing one.
  - **`stack` empty or `undecided`**: do not set up sdlc now. Run the spec through handoff; the build stage then pauses for setup (see Build with sdlc).
- Save the answers in `rspec.json` as `"autopilot": {"enabled": true, "rules": {…}}` (after init has created it) and create `<spec>/autopilot-log.md` from `${CLAUDE_PLUGIN_ROOT}/templates/autopilot-log.md`.

**Rules** (`autopilot.rules`), and what each gate does with them:

| Rule | Gate | Values |
|---|---|---|
| `read_oss_code` | init: clone an open-source product's code | `true` / `false` |
| `features`, `mvp_max`, `retire_used_features` | features approval | `approve-as-proposed`: approve the list if MVP ≤ `mvp_max`; above it, cut the lowest-value MVP features to Later until it fits, each logged. Modernize: a feature that still has users is never retired unless `retire_used_features` is true; otherwise keep it MVP and park it |
| `adrs` | ADR approval in handoff | `accept-recommended`: accept each ADR's recommended decision. `park`: leave them Proposed and stop before the build plan |
| `build_engine` | build engine in handoff | `sdlc`, `claude-code` or `none` |
| `accept_risks` | readiness items that can only be closed by accepting a risk | `false` (default): park them. Never `true` for security or privacy items |

**At every gate:** apply the rule, write the decision into the spec as usual (e.g. ADR `Status: Accepted (autopilot: accept-recommended)`), and add a line under `## Decisions` in the log: date, gate, what was decided, rule. When no rule covers a decision, take the safe default (keep a feature, keep a risk open), add `- [ ] <what needs deciding>` under `## Parked`, and continue with everything that does not depend on it.

**The build** runs with `--autopilot` appended to each `sdlc:start` request, so sdlc does not stop for its own approvals.

**Still stops:** check errors not fixed after one attempt, a test still failing after a fix attempt, anything needing credentials or a login, usage limits. Save the checkpoint with `status: paused` and report. **Never automatic:** deploying to production; sdlc's go-ahead for it stays with the user.

**At the end**, report the parked count from `progress.py` first: the spec or build is not finished while anything is parked. The user resolves parked items (checks them and writes the decision) and runs `/rspec:pipeline continue`.

**Running without a terminal:** `claude -p "/rspec:pipeline --autopilot rspec-autopilot.json"` with the allowed tools in the README, or `/loop /rspec:pipeline continue` to keep it going across sessions.

## Approval gate

`rspec:features` ends by asking the user to approve the feature list. Set `status` to `awaiting-approval` and end the turn. This holds across sessions: a later `continue` with status `awaiting-approval` shows the MVP list again and asks for approval. Never approve on the user's behalf, and never treat "continue", "run everything" or silence as approval of the list. The only exception is autopilot, where the user approved in advance by setting a rule: apply it and log it. When the user explicitly approves (with or without adjustments), finish step 6 of `rspec:features`, set `status` to `running` and resume at `stories`.

## ADR approval gate

`rspec:handoff` starts by asking the user to accept, change or reject each proposed ADR. Set `status` to `awaiting-approval` while waiting and end the turn; the same rules as the features gate apply. Resume when every ADR is Accepted or Rejected.

## Build with sdlc

When `next` is `build` (stage `handoff`, `build.engine` = `sdlc`) and `.sdlc/config.json` is missing, set up sdlc first. Interactive: run `sdlc:setup` as in handoff, giving it the stack recorded in `rspec.json` → `stack`. Under autopilot: set `status` to `paused` and tell the user to run `/sdlc:setup` with that stack (from the accepted stack ADR), then `/rspec:pipeline continue`.

Then take the first pending slice:
1. **Not started** (no `sdlc_feature`): run `sdlc:start` with the Skill tool and this request: "Build slice <N> (<name>) of <spec>/build-plan.md: features <IDs>, stories in <spec>/features/. Follow the rspec section of CLAUDE.md: one backlog part per feature, each AC citing `<spec>/features/<file>.md §<ID>`." Once sdlc has created its feature, record its name in `<spec>/rspec.json` → `build.slices.<N>` (the newest `.sdlc/state/*.md` with `Status: active`).
2. **Started, not done**: run `sdlc:start` with no new request so sdlc resumes its active feature.
3. sdlc runs its own phases, approvals and stops. When it stops for the user, end the turn with `status` `running`; `/rspec:pipeline continue` brings it back here.
4. **Done** (sdlc status `done`): set `status: done` in the frontmatter of each story in that slice, add a line to `<changelog>`, and go to the next pending slice.

When every slice is done, `next` becomes `readiness` (goal `production` with open checklist items) or `check`; continue below.

## Production readiness (goal `production`)

When `next` is `readiness`, `pending` lists the categories of `<spec>/production-readiness.md` that still have unchecked items. Take them in order:
1. With sdlc: run `sdlc:start` with "Production readiness: <category> for <working name>: <the unchecked items, verbatim>. Each item needs evidence (a test, CI job, alert, runbook or document)." Record the sdlc feature name in `rspec.json` → `build.readiness.<category>`; resume it as for slices. Without sdlc: list the open items to the user and stop; they are done by hand.
2. When the change is done, check each item it proved and add its evidence after the item (`- [x] Restore drill: docs/runbooks/restore.md, 2026-11-05`). Leave unproved items unchecked and say why.
3. Never check an item without evidence. Only the user may accept a risk instead; record that as `(accepted risk: <reason>, by <user>)`.

The pipeline finishes only when no item is open. With engine `claude-code` or `none`, the pipeline finishes after the handoff check and the user builds from the plan.

## Pause and stop

Running subagents cannot be cancelled; let the current batch finish, save its results, then:
- **Pause**: set `status` to `paused`, keep `stop_after`, and reply with what is done, what is pending, and "run `/rspec:pipeline continue` (in any session) to resume".
- **Stop**: set `status` to `stopped`, clear `stop_after`, and reply with the same summary. A later `/rspec:pipeline` resumes from the saved stage and pending units, as a new run.

If the user interrupts mid-turn and says nothing else, treat it as pause.

## Finish

After `rspec:check` at stage `handoff` (and, with sdlc, after the last slice), set `status` to `done` and reply with:
- counts: modules, features (MVP / Later / Drop), stories, operations and schemas, ADRs. Take every count from the files (the `check_spec.py` summary line, or by counting rows and files yourself), never from a subagent's reply;
- the build slices from `<spec>/build-plan.md` and, with sdlc, which shipped; otherwise how to start building slice 1;
- with goal `production`: the readiness checklist status (all checked, with evidence) or the open items;
- check result (zero errors; list warnings);
- open questions still marked `unknown`.

## Rules

- Never restart or overwrite an existing spec without asking.
- The rules in the `reverse-spec` skill (writing rules, legal notes, one subagent batch per message) apply at every stage.
