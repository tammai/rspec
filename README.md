# rspec

A Claude Code plugin that turns an existing product into a spec you can rebuild from, for learning or personal use. It researches the product, picks an MVP with you, and writes feature stories and technical docs into your repo, in your own words.

## Quick start

```
/plugin marketplace add tammai/rspec
/plugin install rspec@rspec
```

Then, in your project folder (a new repo, or an sdlc monorepo):

```
/rspec:pipeline Trello
```

It runs every step and stops for your approval twice (the feature list, then the architecture decisions), or if a check fails. Stop any time and continue later, even in a new session, with `/rspec:pipeline continue`. You can also just say "clone Linear to learn": the `reverse-spec` skill picks it up and suggests the next step.

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
| Non-functional requirements | Measurable targets grouped by ISO/IEC 25010 quality characteristic |
| Architecture decisions | ADRs based on Michael Nygard's format, plus date and alternatives considered |
| Traceability | Every operation, schema and NFR names the feature IDs (`F-ISS-01`) it serves; `/rspec:check` verifies the links |
| Evidence | Every fact tagged `[docs]`, `[observed]`, `[inferred]` or `[3p]`; research and story files list their sources |
| Changelog | [Keep a Changelog](https://keepachangelog.com/) |

## Building from the spec

`/rspec:handoff` asks how you want to build:

- **With the [sdlc](https://github.com/tammai/sdlc) plugin** (recommended when installed): `/rspec:pipeline continue` hands each slice of `docs/build-plan.md` to `/sdlc:start`, which defines, builds, reviews and ships it. Its acceptance criteria cite the rspec stories, and the pipeline marks stories done as slices ship, across sessions. If the repo isn't set up for sdlc yet, handoff runs `/sdlc:setup` first.
- **With Claude Code directly**: ask it to "build slice 1 from docs/build-plan.md". The `CLAUDE.md` section tells it to write one test per acceptance criterion, follow the contracts and accepted ADRs, and update each story's `status`.

Content rules: write in your own words, cite a source for every claim, never copy the original's code, text or images, give the rebuild its own name and logo, and keep other people's personal data out. See [legal notes](references/legal-notes.md) (not legal advice).

## Contributing

Run `python -m unittest discover tests` and `claude plugin validate .` before a PR. Releases follow [RELEASE.md](RELEASE.md) and [SemVer](https://semver.org/).

MIT licensed.
