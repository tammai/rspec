# rspec

A Claude Code plugin that turns an existing product into a spec you can build from. Two tracks:

- **rspec**: reverse-spec someone else's product, to learn from it, use it yourself or run it as a service.
- **modernize**: move your own product to a new stack, with parity, data migration and a cutover plan.

rspec writes the spec, not the code. When the spec is done it can hand the build to the [sdlc](https://github.com/tammai/sdlc) plugin, slice by slice. It researches the product, picks an MVP with you, and writes feature stories and technical docs into your repo, in your own words.

## Quick start

```
/plugin marketplace add tammai/rspec
/plugin install rspec@rspec
```

Then, in your project folder (a new repo, or an sdlc monorepo):

```
/rspec:pipeline Trello
```

It first asks which track. It runs every step and stops for your approval twice (the feature list, then the architecture decisions), or if a check fails. Stop any time and continue later, even in a new session, with `/rspec:pipeline continue`. You can also just say "clone Linear to learn": the `reverse-spec` skill picks it up and suggests the next step.

Needs Python 3 (`python3` or `python`). The [Playwright](https://github.com/microsoft/playwright-mcp) MCP is optional; it lets the plugin look at the real UI, read-only.

Update with `/plugin marketplace update rspec`. To try a local checkout: `claude --plugin-dir /path/to/rspec`.

## Commands

| Command | Does |
|---|---|
| `/rspec:pipeline [product]` | Everything below, in order. Also `continue`, `pause`, `stop`, `status`, `--until <stage>` |
| `/rspec:init <product>` | Goal, focus, official sources, `docs/` skeleton |
| `/rspec:discover` | Researches each module in parallel, maps the screens |
| `/rspec:features` | Feature list with MVP / Later / Drop, **waits for your approval** |
| `/rspec:stories` | A story and acceptance criteria for each MVP feature |
| `/rspec:tech` | OpenAPI and JSON Schema contracts, non-functional requirements, proposed ADRs |
| `/rspec:handoff` | **Asks you to accept the ADRs** and how to build (sdlc or Claude Code), writes the build plan and a `CLAUDE.md` section |
| `/rspec:check` | Validates the spec |

## What you get

In a single repo:

```
docs/
  rspec.json         state, layout and pipeline checkpoint
  README.md          scope, sources, disclaimer
  research/          notes per module, with sources
  screens.md         sitemap and main flows
  features.md        feature list and priorities
  features/          one story file per MVP feature
  openapi.json       API contract (+ asyncapi.json for realtime events)
  schemas/           one JSON Schema per entity
  api.md  data-model.md  nfr.md   readable summaries
  decisions/         ADRs
  build-plan.md      MVP in dependency order, in vertical slices
CLAUDE.md            how Claude Code should build from the spec
CHANGELOG.md
```

In an [sdlc](https://github.com/tammai/sdlc) monorepo (detected from `.sdlc/config.json`, `apps/` or `packages/api-contract/`), each part goes where that layout expects it:

| Part | Location |
|---|---|
| The SRS (everything above except contracts and ADRs) and its changelog | `docs/specs/<working-name>/` |
| `openapi.json`, `asyncapi.json`, `schemas/` | `packages/api-contract/v1/` |
| ADRs | `docs/adr/` |

## Standards

The spec is a reverse-engineered software requirements specification. It uses these formats:

| Part | Standard |
|---|---|
| User stories | "As a <role>, I want <capability> so that <benefit>", with YAML frontmatter (`id`, `priority`, `depends_on`, `status`) |
| Acceptance criteria | Gherkin-style "Given …, when …, then …", one test each |
| API | [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0); realtime events in [AsyncAPI 3.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0) |
| Data model | [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) per entity, relations as a Mermaid `erDiagram` |
| Non-functional requirements | Measurable targets grouped by ISO/IEC 25010 quality characteristic, each with the test, monitor or review that verifies it |
| Security (goal `production`) | STRIDE threat model per entry point; every threat mitigated by an NFR or a feature |
| Data migration (modernize) | Old store → new entity mapping (M-01, …), each with a transform and a validation; rehearsal and rollback |
| Cutover (modernize) | Plan per strategy (rewrite, strangler fig, refactor in place) with a required rollback section; parity proved by characterization tests against both systems |
| Production readiness (goal `production`) | Checklist across security, performance, reliability, observability, operations, privacy, accessibility (WCAG 2.2 AA) and legal; each item checked only with evidence |
| Architecture decisions | ADRs based on Michael Nygard's format, plus date and alternatives considered |
| Traceability | Every operation, schema and NFR names the feature IDs (`F-ISS-01`) it serves; `/rspec:check` verifies the links |
| Evidence | Every fact tagged `[docs]`, `[observed]`, `[inferred]` or `[3p]`; research and story files list their sources |
| Changelog | [Keep a Changelog](https://keepachangelog.com/) |

Content rules: write in your own words, cite a source for every claim, never copy the original's code, text or images, give the rebuild its own name and logo, and keep other people's personal data out. See [legal notes](references/legal-notes.md) (not legal advice).

## Building from the spec

`/rspec:handoff` asks how you want to build:

- **With the [sdlc](https://github.com/tammai/sdlc) plugin** (recommended when installed): `/rspec:pipeline continue` hands each slice of `docs/build-plan.md` to `/sdlc:start`, which defines, builds, reviews and ships it. Its acceptance criteria cite the rspec stories, and the pipeline marks stories done as slices ship, across sessions. If the repo isn't set up for sdlc yet, handoff runs `/sdlc:setup` first.
- **With Claude Code directly**: ask it to "build slice 1 from docs/build-plan.md". The `CLAUDE.md` section tells it to write one test per acceptance criterion, follow the contracts and accepted ADRs, and update each story's `status`.

## Modernize track

For your own product. `/rspec:init` asks for the source repos, current and target stack, why you are modernizing, and the strategy (default **full rewrite**; strangler fig or refactor in place on request). Then:

- discovery reads your code (routes, jobs, models, migrations, integrations) and tags facts `[code]` with `path:line`;
- features become MVP = parity required at cutover, Later = after cutover, Drop = retire;
- stories describe current behaviour, so their criteria become characterization tests run against both systems;
- `/rspec:tech` adds `data-migration.md`; `/rspec:handoff` adds `cutover-plan.md` and a Cutover category in the readiness checklist;
- the goal defaults to `production`, so the pipeline finishes only when cutover readiness is proved.

## Goal `production`

`/rspec:init` asks for the goal. `learn` and `personal-use` scope the MVP down. `production` is for a rebuild that will serve real users:

- the MVP keeps account security, roles and permissions, an audit trail, data export and deletion;
- `/rspec:tech` adds a threat model, and every NFR must say how it is verified;
- `/rspec:handoff` writes `production-readiness.md`, and after the last build slice the pipeline hands each open category to sdlc. It is done only when every item is checked with evidence.

The plugin makes production work explicit and checked; it does not replace a security review, load testing on your infrastructure or legal advice.

## Contributing

Run `python -m unittest discover tests` and `claude plugin validate .` before a PR. Releases follow [RELEASE.md](RELEASE.md) and [SemVer](https://semver.org/).

MIT licensed.
