# rspec

A Claude Code plugin that turns an existing product into a spec you can rebuild from, for learning or personal use. It researches the product, picks an MVP with you, and writes feature stories and technical docs into your repo, in your own words.

## Quick start

```
/plugin marketplace add tammai/rspec
/plugin install rspec@rspec
```

Then, in an empty project folder:

```
/rspec:pipeline Trello
```

It runs every step and stops for your approval of the feature list, or if a check fails. Stop any time and continue later, even in a new session, with `/rspec:pipeline continue`. You can also just say "clone Linear to learn": the `reverse-spec` skill picks it up and suggests the next step.

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
| `/rspec:tech` | API, data model, non-functional requirements, proposed ADRs |
| `/rspec:check` | Validates the spec |

## What you get

```
docs/
  rspec.json         state and pipeline checkpoint
  README.md          scope, sources, disclaimer
  research/          notes per module, with sources
  screens.md         sitemap and main flows
  features.md        feature list and priorities
  features/          one story file per MVP feature
  api.md  data-model.md  nfr.md
  decisions/         ADRs
CHANGELOG.md
```

## Standards

The spec it writes follows these formats:

| Part | Standard |
|---|---|
| User stories | "As a <role>, I want <capability> so that <benefit>", with testable `- [ ]` acceptance criteria |
| Architecture decisions | ADRs based on Michael Nygard's format (status, context, decision, consequences), plus date and alternatives considered |
| Data model | Mermaid `erDiagram` |
| Non-functional requirements | Measurable targets (a number or a clear pass/fail), one ID each (`NFR-01`) |
| Changelog | [Keep a Changelog](https://keepachangelog.com/) |
| Feature IDs | `F-<MODULE>-<NN>`, e.g. `F-ISS-01`, never reused |
| Evidence | Every fact tagged `[docs]`, `[observed]`, `[inferred]` or `[3p]`; research and story files list their sources |

Content rules: write in your own words, cite a source for every claim, never copy the original's code, text or images, give the rebuild its own name and logo, and keep other people's personal data out. See [legal notes](references/legal-notes.md) (not legal advice).

## Contributing

Run `python -m unittest discover tests` and `claude plugin validate .` before a PR. Releases follow [RELEASE.md](RELEASE.md) and [SemVer](https://semver.org/).

MIT licensed.
