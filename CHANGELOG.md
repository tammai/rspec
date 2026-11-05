# Changelog

All notable changes to the rspec plugin. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

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
