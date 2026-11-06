# Changelog

All notable changes to the rspec plugin. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

## [0.9.0] - 2026-11-06
### Changed
- **Full spec by default.** New `scope` setting: `full` (default) writes a story and contracts for every feature except Drop; MVP decides only what is built first. `mvp` keeps the old MVP-only spec. Specs made before 0.9.0 have no `scope` and stay MVP-only; add `"scope": "full"` to extend one.
- Stories are written in rounds of batches of about 10 per module, MVP first, so a resume always has the MVP complete. A Later feature may depend on MVP or Later features; an MVP feature still depends only on MVP.
- The build plan is grouped into releases: release 1 is the MVP, Later features follow in releases 2 and up. `--until release-<N>` stops the build after a release.
### Added
- **Deployment target.** `/rspec:init` and autopilot ask where the rebuild will run (`deploy`: Cloudflare Workers, Vercel, a VPS, local only…). The stack ADR must fit it and say which targets its choice rules out, and sdlc setup gets it. `/rspec:check` warns from the tech stage on when it is empty.

## [0.8.5] - 2026-11-06
### Fixed
- sdlc is never set up before the spec is finished: the stack always comes from the spec's accepted stack ADR. 0.8.4 still set up sdlc before the run when a stack was given up front; a given stack is now only a preference the ADR weighs. Under autopilot the build pauses once after handoff for `/sdlc:setup`.

## [0.8.4] - 2026-11-06
Fixes found by the end-to-end run building Linear with sdlc.
### Fixed
- The stack is decided once, by the user, for both rspec and sdlc. Before, autopilot asked for `/sdlc:setup` before the run, and setup scaffolded a stack that the spec's ADR then had to adopt. Now, with a stack given up front, setup uses it and the stack ADR records it; with the stack undecided, setup waits until the ADRs have chosen it, and the build stage pauses for it.
- Handoff writes the accepted stack ADR's choice into `rspec.json` → `stack`; `/rspec:check` warns at handoff when it is still empty.

## [0.8.3] - 2026-11-06
Fixes for four bugs found by bug-hunter, each reproduced by a separate verifier.
### Fixed
- `check_spec.py` and `progress.py` run from inside the spec folder (`.` or no argument) now find the contracts and ADRs; before, they looked in `docs/docs/` and could pass an invalid contract as OK.
- `depends_on: F-X-01` written as a single value counts as a one-item list, instead of being split into characters.
- Files saved with a UTF-8 BOM (Windows PowerShell 5, some editors) are read correctly; before, a story lost its frontmatter and rspec.json failed to parse.
- An escaped pipe (`\|`) in a Markdown table cell no longer shifts the columns of features.md, nfr.md, threat-model.md or data-migration.md.

## [0.8.2] - 2026-11-06
Fixes for building with sdlc, found by the Linear end-to-end run.
### Fixed
- With sdlc, the build plan is cut so that no slice has more than 10 acceptance criteria; a bigger story is a slice of its own. Before, handoff also asked for 3–8 slices, which forced oversized ones.
- If the engine becomes sdlc after the plan was cut, `progress.py` sends the pipeline back to re-cut the slices not yet started, instead of building oversized ones.
- Autopilot with build engine sdlc asks for `/sdlc:setup` before the run starts (headless: stops at once), instead of stalling at setup's own questions mid-run.

## [0.8.1] - 2026-11-06
Fixes from an end-to-end autopilot run on Linear.
### Fixed
- `progress.py` reports `next: done` once the pipeline has finished, instead of asking for the check again.
- `/rspec:check` reports every dependency cycle in one run, not one per run.
- Story writers no longer create cycles between modules: modules are put in dependency order and a feature may depend only on its own or earlier modules.
- The api and data-model agents share one entity list, so `$ref`s match the schema files.
- `init_spec.py --name` sets `working_name`.
- Handoff with build engine `none` still writes the CLAUDE.md section, matching `progress.py`.
### Changed
- `/rspec:check` does not ask under autopilot: it fixes errors once and parks the rest.
- The explorer, story-writer and tech-analyst agents can use Edit.
- Feature behaviour lines are capped at about 20 words.
- Reported counts come from the files, never from a subagent's own report (an agent miscounted its NFRs).

## [0.8.0] - 2026-11-05
### Added
- Autopilot: `/rspec:pipeline --autopilot [rules.json]` runs unattended. It asks everything once (or reads `rspec-autopilot.json`), applies your rules at every gate (features, ADRs, build engine, risks), logs each decision in `autopilot-log.md` and parks what no rule covers. The build runs sdlc with `--autopilot`. Production deploys are never automatic.
- `/rspec:check` and `progress.py` report parked decisions; headless usage documented in the README.

## [0.7.0] - 2026-11-05
### Added
- Modernize track for your own products: `/rspec:pipeline` asks for the track (rspec or modernize) when it starts a spec. Modernize collects source repos, current and target stack, drivers and strategy (rewrite by default, strangler fig or refactor in place), and defaults to goal `production`.
- Discovery from code (`[code]` tags with `path:line`), parity-based priorities, stories as characterization of current behaviour.
- Open-source products in the rspec track: `/rspec:init` offers to read the code, pinned to a commit; discovery and tech learn from routes, models and migrations and copy nothing; `/rspec:check` requires the repo and commit.
- `data-migration.md` (mapping with a validation per row) from `/rspec:tech`; `cutover-plan.md` (rollback required) and a Cutover readiness category from `/rspec:handoff`; `/rspec:check` enforces them.

## [0.6.0] - 2026-11-05
### Added
- `goal: production` for rebuilds that will serve real users: prioritization keeps account security, permissions, audit trail, data export and deletion in the MVP.
- NFRs have a Verification column (test, monitor or review); required for every NFR in production specs.
- `threat-model.md` (STRIDE per entry point, each threat mitigated by an NFR or feature) from `/rspec:tech` in production specs.
- `production-readiness.md` from `/rspec:handoff`: security, performance, reliability, observability, operations, privacy, accessibility and legal items. After the last slice the pipeline hands each open category to sdlc and finishes only when every item is checked with evidence.

## [0.5.0] - 2026-11-05
### Added
- sdlc monorepo layout: the SRS goes to `docs/specs/<name>/`, contracts to `packages/api-contract/v1/`, ADRs to `docs/adr/`, the spec changelog into the spec folder. Detected from `.sdlc/config.json` packages, `apps/` or `packages/api-contract/`; stored as `paths` in `rspec.json`.
- `scripts/init_spec.py` (cross-platform) replaces `init_spec.sh`; the check and progress scripts find the spec in `docs/` or `docs/specs/<name>/`.
### Changed
- Skills, agents and the CLAUDE.md sections use the layout paths instead of fixed `docs/` paths. Specs made before 0.5 keep working: no `paths` means the single-repo layout.

## [0.4.0] - 2026-11-05
### Added
- Build with sdlc: `/rspec:handoff` asks for the build engine (sdlc, Claude Code or none), runs `/sdlc:setup` when needed, keeps slices to about 10 acceptance criteria and writes an sdlc-specific `CLAUDE.md` section.
- `/rspec:pipeline` gains a build step: one `/sdlc:start` per build-plan slice, resumed across sessions from sdlc's own state files; stories are marked done as their slice ships.

## [0.3.0] - 2026-11-05
### Added
- `/rspec:handoff` stage: ADR approval gate, `docs/build-plan.md` (MVP in dependency order, in vertical slices) and a `CLAUDE.md` build section.
- Machine-readable contracts from `/rspec:tech`: `docs/openapi.json` (OpenAPI 3.1), `docs/schemas/*.schema.json` (JSON Schema 2020-12), `docs/asyncapi.json` (AsyncAPI 3.0) for realtime events.
- Traceability: operations, schemas and NFRs list the feature IDs they serve (`x-features`); `/rspec:check` validates the JSON and the IDs.
- Story frontmatter (`id`, `module`, `priority`, `depends_on`, `status`) and Given / When / Then acceptance criteria; `/rspec:check` rejects dependency cycles and MVP features that depend on Later ones.
- `progress.py --build-order` and build status counts, so a build can span sessions.
### Changed
- README rewritten as a quick start, with Standards and Building sections.
- NFRs grouped by ISO/IEC 25010 quality characteristic.
- Specs made with 0.2: re-run `/rspec:stories` to add story frontmatter and `/rspec:tech` to add the contracts; `/rspec:check` says which.
### Security
- `module-explorer` has an explicit tool list again (no Bash, read-only browser tools) and treats web content as untrusted.
- `/rspec:check` warns when a research file contains an email address.
### Fixed
- Skills fall back to `python` when `python3` is not found.

## [0.2.0] - 2026-11-05
### Added
- `/rspec:pipeline` drives the whole spec end to end, with pause, stop, status and continue across sessions (`scripts/progress.py`, checkpoint in `docs/rspec.json`).
- Marketplace manifest, install instructions, release runbook, tests for the scripts.
### Fixed
- Agent frontmatter now parses; agents previously lost their description, model and tools.
- `module-explorer` can use browser MCP tools.
- `/rspec:check` catches every leftover story template placeholder.
- Skills launch agents by their namespaced names (`rspec:...`).
### Changed
- All text in English; default docs `lang` is `en`; section headings stay in English.

## [0.1.0]
- First version.
