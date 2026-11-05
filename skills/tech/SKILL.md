---
name: tech
description: >
  This skill should be used when the user runs /rspec:tech or asks for the API,
  data model, non-functional requirements, architecture or ADRs of the product being
  reverse-specced. Runs three tech-analyst subagents in parallel (api, data-model, nfr)
  and drafts proposed ADRs for the rebuild.
metadata:
  version: "0.3.0"
---

# /rspec:tech

Works best at stage `stories`; allowed from `features-approved`.

1. Read `docs/rspec.json`. If `stack` is empty, ask the user for the intended stack in one question (they may answer "undecided").
2. Launch `rspec:tech-analyst` subagents **in a single message**, with `area` set to `api`, `data-model` and `nfr` (on resume, only the pending areas; skip to step 4 if only `adrs` is pending). Give each: product, `lang`, `focus`, `stack`, sources from rspec.json, the list of research files, `docs/features.md`, its area (the agent knows which files to write), and the absolute path of `${CLAUDE_PLUGIN_ROOT}`.
3. When they return, reconcile: every `$ref` in `openapi.json` points to an existing file in `docs/schemas/`; every MVP feature appears in some `x-features` (UI-only features may be served by schemas alone; say so in `api.md`); NFRs cover each `focus` area. Run the check script, which validates the JSON and the `x-features` IDs.
4. Draft ADRs in `docs/decisions/` from `${CLAUDE_PLUGIN_ROOT}/templates/adr.md`, status `Proposed`, numbered from the next free `NNNN`. One ADR per decision the original product made that the rebuild must also make, typically: data store, realtime/sync approach, auth, ID scheme, API style, search. Context = what the original does (tagged); Decision = recommendation for the user's stack and goal.
5. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .`; fix errors.
6. Set `stage` to `tech`, add a CHANGELOG line. Reply with the ADR titles, the 2–3 decisions the user should confirm, and next step `/rspec:handoff`.
