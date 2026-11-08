# Changelog

All notable changes to the rspec plugin. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]
### Added
- Shared contracts v1 vendored byte-identical in `contracts/v1/` (contracts 1.0.0), with a test that fails when the copy drifts from its `MANIFEST`.
- **Criterion IDs** (contracts C1): every acceptance criterion starts with `**F-<CODE>-<NN>.AC<n>**`, never renumbered or reused.
- `scripts/migrate_criteria.py <spec>`: gives the criteria of an existing spec their IDs in file order, turns `Edge cases` into `Failure modes` lines marked `→ TODO` for the next `/rspec:stories` pass, moves text after a criterion's tag (`repo@commit path:line` citations) unchanged into `Sources`, adds the missing story sections, and changes nothing on a second run.
- **Departures registry** (contracts C5): features approval writes `<spec>/departures.yaml`, one `D-<nnn>` entry per Drop or accepted simplification; story `Differences from the original` lines link them. A difference found later (a story writer's `Open: departure:` note, or an unlinked Differences line in an older spec) is decided by the user once, at the end of `/rspec:stories`; autopilot proposes and parks it. `check_spec.py` errors on a Differences line without a link, a link to a missing entry and an entry without `decided_by`; a proposed entry (autopilot) is a warning until handoff and an error from then on. The lock lists each criterion's departures.
- **PRD without a second summary**: with the sdlc engine, handoff writes sdlc's `prd.md` itself, a short paragraph per section linking into the SRS, and tells `/sdlc:setup` to use it as is.
- **Audit covers every tag**: `audit_sample.py` samples `min(25, max(5, 20%))` criteria of each of `[docs]` `[api]` `[observed]` `[code]` `[inferred]` with a fixed seed (it sampled only `[docs]` and `[api]`). The fact-checker re-observes `[observed]` read-only through Playwright when a reference is configured (else checks the research note), checks `[code]` at the pinned commit, and asks of each `[inferred]` criterion whether a source contradicts it and whether the user should decide it (parked under autopilot).
- **Level 1 from the audit**: `audit_sample.py --levels` turns the fact-checker's verdicts into level 1 (sampled and confirmed, or unsampled in a population whose sample has no contradiction; never a criterion with its own finding); `check_spec.py` writes it into the lock while the criterion's text is unchanged.
- **Criteria lock** (contracts C3): `check_spec.py` writes `<spec>/criteria.lock.json` on every passing run. A criterion whose text changed since the last lock drops to level 0 and is listed as `needs re-verify`.
### Changed
- Story template and `story-writer` follow contracts C2: `Failure modes` (each line → a criterion or `MNB-<n>`), `Must never break`, and `Open questions` after `Sources`. `Edge cases` is removed.
- `check_spec.py` checks stories with the vendored `contracts.py`: grammar, example data, one source tag and the C2 sections are errors (they were warnings). `→ TODO` failure modes from migration are warnings.
- Build plan: each slice lists its criterion IDs and names the acceptance bundle (`<spec>/acceptance/`); a slice is done when every criterion with a level 2 test passes it against the build and every other criterion has a builder test. `check_spec.py` warns about a slice that leaves out a criterion ID.
- Both CLAUDE.md templates: cite criterion IDs, never restate them; bundle tests are read-only. The sdlc variant uses `- **AC-001** → F-ISS-01.AC2`; the Claude Code variant says how to run the bundle against the build.

## [0.10.1] - 2026-11-07
### Added
- `/rspec:site` extraction snippets for three things the Apple MacBook Air run had to measure by hand (`references/site-extract.md`):
  - **E. Gradient-filled text:** every headline painted with `background-clip: text`, grouped by fill. On the Apple page it found 14 such headlines in one call: 12 share one gradient and 2 are filled with an image.
  - **F. Scroll-reveal timing:** samples opacity and offset as hidden content scrolls into view, and says whether the effect plays once or follows the scroll. On the Apple page it corrected the hand-made spec: reveals settle in about 600 ms (not 1 s), labels drop 4 px into place while headlines rise, and the headlines follow the scroll.
  - **G. Carousels:** every row that scrolls sideways, with item size, gap, radius, edge bleed, snap and controls. On the Apple page it found 5 carousels; the hand-made pass had spotted 1.
### Changed
- The `/rspec:site` skill runs the new snippets, and the spec template has a headline-fill row, scroll-reveal details under Motion and a Carousels line under Interactions.

## [0.10.0] - 2026-11-07
### Added
- **`/rspec:site <url>`**: a standalone playbook to rebuild a marketing site or landing page with the same taste and UI/UX. It observes one page read-only at 375, 768 and 1440 (and dark mode), runs the read-only extraction snippets in `references/site-extract.md` through Playwright, and writes `docs/site/<name>/site-spec.md` (vibe, tokens, components, section anatomy, interactions, at most ten acceptance criteria), `tokens.json` (W3C DTCG) and `tokens.css`. It takes the system, never the text, images, icons or fonts; licensed fonts get a free substitute. It does not touch the `rspec.json` pipeline.

## [0.9.9] - 2026-11-07
Four Minor frictions the gophish → bigin-phish run surfaced (it reached handoff and met every audit target: facts 97.4%, coverage 92%, 0 contradictions).
### Fixed
- `/rspec:check` errors, instead of silently parsing zero slices, when build-plan.md uses `### Slice N` headings (the parser and template want `## Slice N`). A run once read 88 cut slices as "none".
- The research PII check no longer flags format placeholders and example addresses (`local@domain.tld`, `user@example.com`); a real address is still flagged, now quoted.
- The domain.md roles check skips a placeholder Operations cell (e.g. `_(tech fills)_`), which the features stage leaves for tech to fill.
- The domain.md enumeration check warns when a Name cell matches no schema property of that name (a vacuous pass before), so the Name must be the exact property name.

## [0.9.8] - 2026-11-06
Edge-input robustness, from six bugs the bug-hunter surfaced by reading the scripts (it could not run its repros on Windows; each was reproduced by hand and fixed test-first).
### Fixed
- `scripts/scorecard.py` no longer crashes on a feature row with an empty name (`ZeroDivisionError` in the MVP-name match).
- `scripts/scorecard.py` tokenises names in any script, not just ASCII: a non-English name like "Đăng ký" now yields real words (`{đăng, ký}`) instead of fragments (`{k, ng}`) that let unrelated names collide. English scoring is unchanged (the two v0.9.5 runs still score 90% overlap).
- `/rspec:check` matches build-plan feature coverage by whole ID, so `F-ISS-10` is no longer counted as present when only `F-ISS-100` is in the plan.
- `/rspec:check` reports a clean error instead of a traceback for a contract file whose top level is not a JSON object, for `rspec.json` with `"modules": null`, and for a request body whose `x-entity` schema file is itself invalid JSON.

## [0.9.7] - 2026-11-06
The audit that measured the v0.9.5 runs is now part of the pipeline.
### Added
- **`/rspec:audit`**, run by the pipeline after tech and before handoff. Three subagents in parallel write reports to `<spec>/audit/`:
  - `rspec:fact-checker` checks a fixed-seed sample of 25 `[docs]` and 25 `[api]` criteria (`scripts/audit_sample.py`) against the sources they cite, judging the expected result, not the topic.
  - `rspec:coverage-auditor` builds a reference list from the product's docs navigation and last 12 months of changelog, without reading the spec, and maps it to features.md.
  - `rspec:consistency-auditor` finds contradictions between `domain.md`, stories, features.md, NFRs, ADRs, contracts and the build order.

  The main session fixes the Important findings (retag or correct a fact, add a missing core capability through triage, make files agree with `domain.md` and the accepted ADRs), parks product decisions under autopilot, lists the Minor ones, and writes `audit/summary.md` with the scores. Targets: fact accuracy ≥ 90% with none contradicted, coverage ≥ 90%, no Important contradictions left.
- **Coverage pass before feature approval:** `/rspec:features` runs the coverage auditor before the approval gate and adds a row (or a reasoned Drop) for each missing core or focus capability. The audit later reuses the same reference list.
### Changed
- `progress.py` reports `next: audit` between tech and handoff until `audit/summary.md` exists; `--until audit` stops there. Handoff requires a finished audit.

## [0.9.6] - 2026-11-06
Fixes from auditing the two v0.9.5 Linear runs (fact-check, coverage, consistency): the specs were accurate (82–90%) and covered 85% of Linear's documented capabilities, but each had 16–18 important internal contradictions.
### Added
- **`domain.md`: one source for shared rules.** Written after the feature list is approved: a roles × actions permission table, every enumeration used in more than one place, limits and defaults, identifier formats. Stories, NFRs and contracts use and cite it instead of restating rules. `/rspec:check` errors when an operation's `x-roles` or a schema `enum` differs from it. Most contradictions in the audit were restated rules that drifted (who may create API keys, team key length, an owner role that stories ruled out).
- `/rspec:check` errors when a request body marked `x-entity` uses a field its entity schema lacks, and warns on required server-set fields (`id`, timestamps) that are not `readOnly`.
### Changed
- **Data model first, then the API on top of it.** The tech stage runs data-model and nfr together, then api against the written schemas, so the two no longer drift on field names and owners.
- A cross-module need that `merge_deps.py` cannot add (it would close a cycle) is never dropped silently: split or move a feature, or park it. After the stories, the main session reconciles every story with `domain.md` and the others.
- **The evidence tag is for the expected result**, not the topic: `[docs]` or `[api]` only when the source states that result; otherwise split the criterion or tag it `[inferred]`.
- `progress.py` reports `next: parked`, not `done`, while autopilot decisions are still open; conflicts and still-needed ADRs are parked too.
- Tech agents can run Bash to validate their JSON.
### Fixed
- `scripts/scorecard.py` counts the inferred share over acceptance criteria only (Differences are `[inferred]` by rule), and matches MVP names by shared content words, which agrees with a reading by meaning (90% for the two v0.9.5 runs).

## [0.9.5] - 2026-11-06
One quality bar for every spec, whatever the build engine. It combines the strengths of the two full-scope Linear runs: one tagged 93% of its criteria and kept the MVP on the focus; the other had more concrete criteria and a deployment-aware architecture.
### Changed
- **Acceptance criteria quality bar** (writing-rules.md, story-writer, story template): every criterion uses example data a test can use as is (`ENG-12`, priority Urgent, three selected issues) and ends with its evidence tag.
- **Focus in the MVP:** every focus area gets a step in the core journey, and the MVP holds the features that make that area work end to end, not just one of them.
- **Architecture as concrete without a deployment target:** with `deploy` undecided, the stack ADR recommends a target (and a runner-up) and designs for it; handoff records the accepted one. Tech always drafts a platform ADR with the target's limits and sizes the NFRs to them.
### Added
- `/rspec:check` warns on criteria without an evidence tag and on contracts that mix snake_case and camelCase property names.
- `scripts/scorecard.py` reports the tagged-criteria share (target ≥ 90%).

## [0.9.4] - 2026-11-06
Better evidence and fewer contradictions, from the full-scope Linear runs (43–47% of story facts were `[inferred]`).
### Added
- **`[api]` evidence tag.** Init looks for the product's machine-readable API schema (a public GraphQL schema, an OpenAPI file, typed SDK sources) and records it in `sources.api`. Module explorers and the data-model agent read it first for entities, fields, enums and limits, tagged `[api]`; a fact the schema settles is never `[inferred]`. `scripts/scorecard.py` already counts the tag.
### Fixed
- NFRs are read against the ADRs: tech fixes or flags an NFR a recommended decision cannot meet, and handoff updates NFRs after the ADRs are accepted (the Workers run had offline editing in the NFRs and no offline support in the sync ADR).
- Story writers no longer add capabilities that no feature row describes; they note the idea as an open question for triage (the Workers run grew an "Asks" form that features.md did not have).

## [0.9.3] - 2026-11-06
Steadier results between runs, from comparing the two full-scope Linear runs (231 vs 182 features, 55% MVP overlap by name).
### Changed
- **Modules follow the product's own navigation.** Discover takes one module per top-level area of the product's sidebar, menu and settings (6–10 modules), records the page each maps to, and uses features, pricing and changelog only to place features. A rules file can pin `modules` so repeat runs share one split.
- **One feature size.** A feature is one capability a user would name, deliverable in one build change: about 3–8 acceptance criteria. Smaller items merge (status, priority and assignee are one "issue properties" feature); bigger ones split.
- **MVP from the core journey.** features.md starts with a `## Core journey` of 6–10 steps; the MVP is the features those steps touch plus their dependencies, and each MVP reason cites its step.
- **Slices by criteria budget.** Without sdlc a slice holds about 30 acceptance criteria (0.9.2 capped it at 8 features); with sdlc it stays at 10 per slice, since sdlc takes about 10 per change.
### Added
- `scripts/scorecard.py` scores a finished spec, or compares two runs: MVP overlap by feature name, feature-count spread, inferred share of facts, slices over budget. Targets: overlap ≥ 80%, spread ≤ 15%, inferred ≤ 30%, no slice over budget.

## [0.9.2] - 2026-11-06
Fixes found by the full-scope end-to-end runs on Linear.
### Added
- **Triage.** `/rspec:features triage F-INT-23=Later …` moves features between Drop, Later and MVP at any stage. It writes only the new stories, adds only their contracts (tech add mode) and slots them into the build plan, without rerunning the pipeline. A priority edited by hand in features.md shows up as `next: triage` in `progress.py`, and `/rspec:pipeline` runs it. Drop is a recorded decision ("outside the focus" is a valid reason) that you can triage later.
- Story writers put a need on a later module in `also_needs`; `scripts/merge_deps.py` moves it into `depends_on` after the last round unless it would close a cycle or make an MVP feature need a Later one.
- `ui_only: true` in a story's frontmatter: the check no longer expects a contract for a feature with no data of its own.
- features.md has a `Research ID` column, so story writers find a renumbered feature in its research file.
### Fixed
- `/rspec:check` resolves every `$ref` in the contracts and errors on one that points nowhere.
- Without sdlc, a slice holds at most 8 features (before: 3–8 slices in all, which gave slices of 50 features at full scope); the check warns on a bigger one. Releases group around one area where the dependencies allow.
- The api and data-model agents get one field-name casing (camelCase unless the stack says otherwise).
- The check errors when the build plan still includes a Drop feature.

## [0.9.1] - 2026-11-06
### Fixed
- Autopilot builds no longer pass `--autopilot` to `sdlc:start`. In sdlc that flag marks a headless session started by its `autopilot.py`, which runs one part and ends, so every slice needed extra resumes before review and ship. The pipeline now asks sdlc for autopilot in words, which runs every part, Review and Ship in the same session.

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
