# Changelog

All notable changes to the rspec plugin. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

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
