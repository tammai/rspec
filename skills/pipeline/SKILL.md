---
name: pipeline
description: >
  This skill should be used when the user runs /rspec:pipeline or asks to run the
  whole reverse spec end to end, or to pause, stop, resume, continue or check the
  status of it, including in a new session ("do the full spec for Linear", "run all
  rspec steps", "continue the spec", "pause the pipeline", "where is the spec at").
  Drives init → discover → features → stories → tech → handoff → check from where it left off,
  pausing at the features and ADR approval gates.
argument-hint: "[product | continue | pause | stop | status] [--until <stage>]"
metadata:
  version: "0.3.0"
---

# /rspec:pipeline

Drive the reverse spec to a finished, checked spec, across as many sessions as it takes. Each stage is done by its own skill; this skill sequences them, saves a checkpoint and stops when the user asks or something needs them.

## Arguments (`$ARGUMENTS`)

| Argument | Meaning |
|---|---|
| empty or `continue` | Start, or resume from the checkpoint |
| `<product>` | Start a new spec for that product (only if `docs/rspec.json` does not exist) |
| `pause` | Pause: save the checkpoint, keep the run's settings, end the turn |
| `stop` | Stop: end this run and clear `stop_after`; a later run starts fresh from the saved stage |
| `status` | Report the checkpoint and pending work; change nothing |
| `--until <stage>` | Stop after that stage (`discover`, `features`, `stories`, `tech`, `handoff`) |

Plain words count too: "pause", "stop here", "carry on", "resume" in the user's language mean the same as the arguments.

## Where things stand

The truth is on disk. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py .` at the start of every turn of this skill, and after each unit of work. It prints JSON with `stage`, `next` (the step to run), `pending` (what that step still has to do: module codes, MVP feature IDs, tech areas, `module-map`, `screens`, `adrs`, `approval`, `adr-approval`, `build-plan`, `claude-md`, `check`) and the saved `pipeline` checkpoint.

The checkpoint lives in `docs/rspec.json`:

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

1. Run `progress.py`. If there is no spec, run `rspec:init` with the product (ask for it if missing).
2. If `pipeline.status` is `running`, the last session ended without pausing. Say so, and treat files written by the last batch as suspect: recheck them (research file has Screens, Features observed and Sources; story passes `check_spec.py`) and redo only the broken ones.
3. Tell the user in two lines: stage, what is done, what is pending, and the next step.
4. Set `status` to `running`, `current` to the next step, then enter the loop.

## Loop

1. Run the next step's skill with the Skill tool: `rspec:discover`, `rspec:features`, `rspec:stories`, `rspec:tech`, `rspec:handoff` or `rspec:check`. Pass the `pending` list and say it is a resume, so the skill does only the pending units and leaves finished files alone.
2. After each batch of subagents: update `last` and `updated`.
3. When the step's skill finishes: confirm with `progress.py` that the stage advanced, and run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .`. If errors remain after one fix attempt, set `status` to `paused`, show the errors and end the turn.
4. If the user has asked to pause or stop, or the finished stage equals `stop_after`, apply Pause/Stop below. Otherwise continue with the next step.

## Approval gate

`rspec:features` ends by asking the user to approve the feature list. Set `status` to `awaiting-approval` and end the turn. This holds across sessions: a later `continue` with status `awaiting-approval` shows the MVP list again and asks for approval. Never approve on the user's behalf, and never treat "continue", "run everything" or silence as approval of the list. When the user explicitly approves (with or without adjustments), finish step 6 of `rspec:features`, set `status` to `running` and resume at `stories`.

## ADR approval gate

`rspec:handoff` starts by asking the user to accept, change or reject each proposed ADR. Set `status` to `awaiting-approval` while waiting and end the turn; the same rules as the features gate apply. Resume when every ADR is Accepted or Rejected.

## Pause and stop

Running subagents cannot be cancelled; let the current batch finish, save its results, then:
- **Pause**: set `status` to `paused`, keep `stop_after`, and reply with what is done, what is pending, and "run `/rspec:pipeline continue` (in any session) to resume".
- **Stop**: set `status` to `stopped`, clear `stop_after`, and reply with the same summary. A later `/rspec:pipeline` resumes from the saved stage and pending units, as a new run.

If the user interrupts mid-turn and says nothing else, treat it as pause.

## Finish

After `rspec:check` at stage `handoff`, set `status` to `done` and reply with:
- counts: modules, features (MVP / Later / Drop), stories, operations and schemas, ADRs;
- the build slices from `docs/build-plan.md`, and how to start building slice 1;
- check result (zero errors; list warnings);
- open questions still marked `unknown`.

## Rules

- Never restart or overwrite an existing spec without asking.
- The rules in the `reverse-spec` skill (writing rules, legal notes, one subagent batch per message) apply at every stage.
