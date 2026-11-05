# Changelog

All notable changes to the rspec plugin. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

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
