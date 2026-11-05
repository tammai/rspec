---
name: reverse-spec
description: >
  This skill should be used when the user wants to recreate, clone, rebuild or
  reverse-engineer an existing app or product for personal use or for learning,
  wants to document the features and technical requirements of an existing
  product, or says things like "recreate app X", "clone X to learn", "remake
  product X", "write a reverse spec for X", "reverse spec", "rebuild Linear/Notion/Trello".
  It explains the rspec pipeline and routes to the right /rspec command based on
  the current state in docs/rspec.json.
metadata:
  version: "0.3.0"
---

# Reverse spec pipeline

Produce an original specification of an existing product, written in the project's own words, that is good enough to rebuild a scoped version of it.

## Stages

| Stage in `docs/rspec.json` | Done by | Next command |
|---|---|---|
| (no docs/rspec.json) | | `/rspec:init <product>` |
| `init` | init | `/rspec:discover` |
| `discovered` | discover | `/rspec:features` |
| `features-approved` | features, after user approval | `/rspec:stories` |
| `stories` | stories | `/rspec:tech` |
| `tech` | tech | `/rspec:handoff` |
| `handoff` | handoff, after ADR approval | build from `docs/build-plan.md`; re-run `/rspec:check` after spec edits |

## Routing

1. If the user wants the whole spec done in one go, hand over to `/rspec:pipeline`.
2. Look for `docs/rspec.json` in the current project.
3. If absent, propose `/rspec:init <product>`; if the user already named the product and goal, start the init workflow directly.
4. If present, report product, stage and counts (run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .`), then propose the next command from the table.
5. Never skip the approval gates: features before stories, ADRs before handoff.

## Rules that apply at every stage

- The plugin's scripts are run with `python3`; if that command is not found (common on Windows), use `python` instead.

- Read `${CLAUDE_PLUGIN_ROOT}/references/writing-rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/legal-notes.md` before writing any spec file.
- Prefer current sources over prior knowledge; products change.
- Parallel work happens only in `discover`, `stories` and `tech`, through the plugin's subagents. Launch all subagents of one batch in a **single message** so they run concurrently. Subagents cannot launch further subagents.
- Each subagent owns exactly one module or area and writes only its own files. The main session merges.
- Update `stage` and `updated` in `docs/rspec.json` at the end of each command, and add a line to `CHANGELOG.md` under `[Unreleased]`.
