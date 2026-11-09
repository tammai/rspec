---
name: init
description: >
  This skill should be used when the user runs /rspec:init or asks to start a
  reverse spec / rebuild of a named product ("start rebuilding Linear",
  "init spec for Trello"). Sets the goal, learning focus and official sources,
  and creates the spec skeleton (single repo or sdlc monorepo layout).
argument-hint: <product name>
metadata:
  version: "0.11.0"
---

# /rspec:init

Product: `$ARGUMENTS`

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py .`. If it reports a stage, a spec already exists: show its product and stage and ask whether to continue that spec or start over. Never overwrite silently.
2. Track: `rspec` (default) or `modernize`, as passed by `/rspec:pipeline` or asked here. For **modernize**, collect instead of the rspec-only items below: the source repo paths or URLs (clone URLs into a sibling folder only with the user's OK), the current stack, the target stack, why modernize (drivers: cost, performance, hiring, security, end of life), the strategy (`rewrite` by default; `strangler` or `refactor` on request), and where usage data lives (analytics, logs) if any. `working_name` is the product's own name; `goal` is `production` unless the user says otherwise. Sources are the code first, then internal docs.
3. Collect (under autopilot, take every answer from the autopilot rules and ask nothing), asking only for what is missing (use AskUserQuestion, one round):
   - `goal`: `learn`, `personal-use`, or `production` (the rebuild will serve real users: adds a threat model, verified NFRs and a production-readiness checklist; also ask who the users are and the expected scale, and record them in `focus`)
   - `focus`: the parts the user most wants to learn or needs (free text, may be empty)
   - `working_name`: a name for the rebuild that is not the original brand (suggest one)
   - `lang`: language of the docs (default: the language the user is writing in)
   - `scope`: `full` (default: a story and contracts for every feature except Drop; MVP only decides what is built first) or `mvp` (MVP features only, for a quick spec)
   - `deploy`: where the rebuild will run (e.g. Cloudflare Workers, Vercel, Netlify, AWS, a VPS or Docker host, mobile app stores, desktop, local only). Ask it even when the stack is undecided: the target constrains the stack (a Workers runtime has no Node filesystem or long-lived processes and favours frameworks with a Workers adapter; a static host needs a separate API). Record the answer and any limits the user names (budget, region, existing account).
   - `stack`: target stack if already decided (optional; a preference the stack ADR weighs against `deploy`)
   - layout: if the repo is an sdlc monorepo (`.sdlc/config.json` lists packages, or `packages/api-contract/` or `apps/` exists), say the spec will go to `docs/specs/<working-name>/`, the API contract to `packages/api-contract/v1/` and ADRs to `docs/adr/`, and confirm. Otherwise the spec goes in `docs/`.
4. rspec track: find official sources with WebSearch: product site, docs/help center, changelog, public API reference, and any official open-source repo. For the API, look for a machine-readable schema (a public GraphQL schema or its introspection file in the vendor's SDK repo, an OpenAPI file, typed SDK sources) and record its URL in `sources.api`: it is the best public evidence for entities, fields and limits. Record URLs, not content. If the user may later record tests against the hosted product (`/rspec:verify`, kind `url`), say now that it is read-only and bound by the product's terms (legal-notes.md, Recording against a reference). If the product is open source, recommend reading its code too (the most precise source for behaviour, data model and API): with the user's OK, clone it into a sibling folder outside this project and pin the commit. Set `code: true`, `sources.repo`, `sources.commit` and `sources.license` (for reference). The code is read to learn from, never copied (see legal-notes.md).
5. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/init_spec.py . --name "<working_name>"` (add `--layout single` or `--layout monorepo` to override detection; modernize: add `--track modernize --strategy <strategy>`). It prints the `paths` it used; from now on `<spec>`, `<contracts>`, `<decisions>` and `<changelog>` mean those paths.
6. Fill `<spec>/rspec.json` (product, track, scope, deploy, strategy and source repos for modernize, working_name, goal, focus, lang, stack, sources, `modules: []`, `stage: "init"`, `updated`: today) and `<spec>/README.md` (replace placeholders; keep the disclaimer).
7. Add `- Started reverse spec of <product>` to `<changelog>`.
8. Reply with a short summary and the next step: `/rspec:discover`.
