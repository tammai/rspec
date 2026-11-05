# rspec: reverse-spec an existing product

A Claude Code plugin for rebuilding a product (for personal use or for learning) by writing a **reverse spec**: observe the original product, then rewrite its features and technical requirements in your own words as documents in your repo.

## Install

In Claude Code:

```
/plugin marketplace add tammai/rspec
/plugin install rspec@rspec
```

Update later with `/plugin marketplace update rspec`. To try a local checkout for one session instead: `claude --plugin-dir /path/to/rspec`.

## Workflow and commands

| Command | What it does | Parallel |
|---|---|---|
| `/rspec:init <product>` | Settle the goal, what you want to learn, and official sources; create the `docs/` skeleton | |
| `/rspec:discover` | Split the product into modules, explore each module, merge into `screens.md` | 1 subagent / module |
| `/rspec:features` | Build `features.md` with IDs and MVP / Later / Drop priorities. **Stops for your approval** | |
| `/rspec:stories` | Write a user story + acceptance criteria for every MVP feature | 1 subagent / module |
| `/rspec:tech` | `api.md`, `data-model.md`, `nfr.md` and proposed ADRs | 3 subagents: api, data, nfr |
| `/rspec:check` | Check the spec: duplicate IDs, MVP features without a story, stories without criteria | |
| `/rspec:pipeline [product \| continue \| pause \| stop \| status] [--until <stage>]` | Run every step above in order. Saves a checkpoint in `docs/rspec.json`, so you can pause, stop and continue in any later session. Waits for your features approval | as each step |

The `reverse-spec` skill activates on its own when you say things like "recreate app X" or "clone X to learn", and tells you the next step based on `docs/rspec.json`.

## Output in your repo

```
docs/
  rspec.json            # state: product, goal, modules, stage
  README.md             # scope + legal notes
  research/<module>.md  # discovery notes, with sources
  screens.md
  features.md
  features/F-ISS-01-*.md
  api.md
  data-model.md
  nfr.md
  decisions/0001-*.md
CHANGELOG.md
```

Feature IDs have the form `F-<MODULE CODE>-<number>` (for example `F-ISS-01`). Each subagent only assigns IDs within its own module, so running in parallel never produces duplicates.

## Requirements

- Claude Code (uses subagents, WebSearch/WebFetch).
- Python 3 for `scripts/check_spec.py` (run its tests with `python -m unittest discover tests`).
- Optional: a browser MCP (Playwright/Chrome) if you want subagents to observe the real UI.

## Principles

Rewrite in your own words, cite a source for every claim, do not copy the original product's code, images or wording, and do not use the original name/logo for the rebuild. See `references/legal-notes.md`. This is not legal advice.
