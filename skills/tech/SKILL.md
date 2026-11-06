---
name: tech
description: >
  This skill should be used when the user runs /rspec:tech or asks for the API,
  data model, non-functional requirements, architecture or ADRs of the product being
  reverse-specced. Runs three tech-analyst subagents in parallel (api, data-model, nfr)
  and drafts proposed ADRs for the rebuild.
metadata:
  version: "0.9.0"
---

# /rspec:tech

Works best at stage `stories`; allowed from `features-approved`.

1. Read `<spec>/rspec.json`. The features in scope are the MVP rows, plus Later rows when `scope` is `full`. The stack ADR must fit `deploy`, the deployment target: name it in the ADR's Context, rule out stacks that do not run well there (e.g. on Cloudflare Workers prefer a framework with a first-class Workers adapter and a Workers-compatible data store such as D1, KV or Durable Objects; Node-only servers, native modules and local SQLite files do not fit), and say which targets the choice rules out. If `deploy` is empty, ask for it in the same question as the stack; under autopilot use "undecided", park it, and let the ADR say which targets its choice fits. If `stack` is empty, ask the user for the intended stack in one question (they may answer "undecided"); under autopilot, use "undecided" and let the ADRs recommend one. When the user gave a stack, the stack ADR recommends it unless the spec rules it out, and says why if it does.
2. Unless `<contracts>/schemas/` already has files, first decide the entities of the features in scope from the features and research: one list of singular kebab-case names with their schema files (`issue` → `schemas/issue.schema.json`). Give the same list to the `api` and `data-model` agents so every `$ref` matches; an agent that needs another entity adds it and says so in its reply. Then launch `rspec:tech-analyst` subagents **in a single message**, with `area` set to `api`, `data-model` and `nfr`, plus `data-migration` in the modernize track (on resume, only the pending areas; skip to step 4 if only `adrs` is pending). Give each: `goal`, `scope` (the feature IDs in scope), `deploy`, `track`, `strategy`, `code` and source repo paths (modernize or open source), product, `lang`, `focus`, `stack`, sources from rspec.json, the list of research files, `<spec>/features.md`, its area (the agent knows which files to write), and the absolute path of `${CLAUDE_PLUGIN_ROOT}`.
3. When they return, reconcile: every `$ref` in `openapi.json` points to an existing file in `<contracts>/schemas/`; every feature in scope appears in some `x-features` (UI-only features may be served by schemas alone; say so in `api.md`); NFRs cover each `focus` area. When `goal` is `production`: every operation in `<contracts>/openapi.json` and every input screen appears as an entry point in `<spec>/threat-model.md` (add missing threats yourself), every threat has a mitigation, and every NFR has a Verification. Modernize track: every old table in the mapping appears in `<spec>/data-migration.md` (migrated or "not migrated" with a reason), and every entity in `<contracts>/schemas/` that holds migrated data is a mapping target. Run the check script, which validates the JSON and the `x-features` IDs.
4. Draft ADRs in `<decisions>/` from `${CLAUDE_PLUGIN_ROOT}/templates/adr.md`, status `Proposed`, numbered from the next free `NNNN`. One ADR per decision the original product made that the rebuild must also make, typically: data store, realtime/sync approach, auth, ID scheme, API style, search. Context = what the original does (tagged); Decision = recommendation for the user's stack and goal.
5. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .`; fix errors.
6. Set `stage` to `tech`, add a line to `<changelog>`. Reply with the counts of operations, schemas and NFRs, taken from the files (never from the subagents' replies), the ADR titles, the 2–3 decisions the user should confirm, and next step `/rspec:handoff`.
