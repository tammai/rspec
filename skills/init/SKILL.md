---
name: init
description: >
  This skill should be used when the user runs /rspec:init or asks to start a
  reverse spec / rebuild of a named product ("start rebuilding Linear",
  "init spec for Trello"). Sets the goal, learning focus and official sources,
  and creates the spec skeleton (single repo or sdlc monorepo layout).
argument-hint: <product name>
metadata:
  version: "0.5.0"
---

# /rspec:init

Product: `$ARGUMENTS`

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py .`. If it reports a stage, a spec already exists: show its product and stage and ask whether to continue that spec or start over. Never overwrite silently.
2. Collect, asking only for what is missing (use AskUserQuestion, one round):
   - `goal`: `learn` or `personal-use`
   - `focus`: the parts the user most wants to learn or needs (free text, may be empty)
   - `working_name`: a name for the rebuild that is not the original brand (suggest one)
   - `lang`: language of the docs (default: the language the user is writing in)
   - `stack`: target stack if already decided (optional)
   - layout: if the repo is an sdlc monorepo (`.sdlc/config.json` lists packages, or `packages/api-contract/` or `apps/` exists), say the spec will go to `docs/specs/<working-name>/`, the API contract to `packages/api-contract/v1/` and ADRs to `docs/adr/`, and confirm. Otherwise the spec goes in `docs/`.
3. Find official sources with WebSearch: product site, docs/help center, changelog, public API reference, and any official open-source repo. Check the repo licence. Record URLs, not content.
4. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/init_spec.py . --name "<working_name>"` (add `--layout single` or `--layout monorepo` to override detection). It prints the `paths` it used; from now on `<spec>`, `<contracts>`, `<decisions>` and `<changelog>` mean those paths.
5. Fill `<spec>/rspec.json` (product, working_name, goal, focus, lang, stack, sources, `modules: []`, `stage: "init"`, `updated`: today) and `<spec>/README.md` (replace placeholders; keep the disclaimer).
6. Add `- Started reverse spec of <product>` to `<changelog>`.
7. Reply with a short summary and the next step: `/rspec:discover`.
