# rspec 0.11.1: rules-recall test (product-rebuild MIGRATION-3.md row 9)

## Why

Request (coordinator, approved by the user 2026-11-09): "product-rebuild 3.0.0 retired its Rule Cards (D2) and promised to port its `rules-recall` eval to rspec as a recall test for OSS-mode discovery (MIGRATION-3.md row 9). … the fixture and one test that measures how much of the known rule set rspec's discovery output records (as the proposal defines), reporting recall, with a threshold only if the proposal sets one."

The proposal is product-rebuild's `docs/rspec-pr/rules-recall/PR.md`. Every rspec check today measures precision (is what the spec says true); none notices a discovery change that finds fewer rules. This adds the one recall measure: a billing codebase with its 33 known rules, and a script that scores a spec written from it.

## Acceptance criteria

- **AC-001** — PR.md "Proposed test" 2: `python3 scripts/rules_recall.py <project-or-spec>` scores the spec against `tests/fixtures/rules-recall/gold.yaml`: a gold rule is found when a `domain.md` line or a `[code]` criterion cites `path:line` inside one of the rule's locations, and the first line prints recall as a share and `found/33`.
- **AC-002** — PR.md 2, strict: a found rule counts for strict recall only when the citing line's own text (citations removed) holds every `values` group; the report lists each found-but-not-strict rule with the values it lacks.
- **AC-003** — a citation counts only with a line: a file-level citation (`path` alone) and a citation from a criterion not tagged `[code]` never find a rule.
- **AC-004** — a `[code]` criterion's citations are those on its own line, on `## Sources` lines naming its ID, and on `## Sources` lines naming no criterion ID.
- **AC-005** — PR.md 3 and the gold-set note: the report names the rspec version and the model tier (`--model`), lists missed rules (ID, rule, `hard` reason) and every citation matching no gold rule (the gold set may be short); it exits 0 whatever the score (the proposal sets no threshold).
- **AC-006** — PR.md "What is here": `tests/fixtures/rules-recall/` holds `reference-src/` byte-identical to product-rebuild's and `gold.yaml` with only its header comment rewritten for this scorer, plus a README with the run procedure.
- **AC-007** — release: version 0.11.1 in both manifests and a CHANGELOG entry crediting product-rebuild MIGRATION-3.md row 9.

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | `tests/test_rules_recall.py` › `test_scores_a_spec_against_the_gold_rules` | `python -m unittest discover tests -p test_rules_recall.py` |
| AC-002 | `tests/test_rules_recall.py` › `test_scores_a_spec_against_the_gold_rules` | `python -m unittest discover tests -p test_rules_recall.py` |
| AC-003 | `tests/test_rules_recall.py` › `test_scores_a_spec_against_the_gold_rules` | `python -m unittest discover tests -p test_rules_recall.py` |
| AC-004 | `tests/test_rules_recall.py` › `test_scores_a_spec_against_the_gold_rules` | `python -m unittest discover tests -p test_rules_recall.py` |
| AC-005 | `tests/test_rules_recall.py` › `test_scores_a_spec_against_the_gold_rules` | `python -m unittest discover tests -p test_rules_recall.py` |
| AC-006 | manual | `diff -r` against product-rebuild's `docs/rspec-pr/rules-recall/reference-src` and `git diff --no-index` of `gold.yaml` (header only); the user's testing rule forbids file-list tests |
| AC-007 | manual | release fields, checked against RELEASE.md's checklist; no meta tests |

## Must never break

- The full suite (`python -m unittest discover tests`) and `claude plugin validate .` pass.
- `reference-src/` line numbers match `gold.yaml`: the fixture is copied, never retyped.

## Decisions

| Decision | Chosen | Ruled out, why |
|---|---|---|
| What "the test" is | A scorer script plus one unit test on a small hand-written spec with exact numbers. The live run (discover, features, stories on the fixture) is manual and stays out of the suite | Running discovery in `unittest`: needs model calls and subagents, and the score decides nothing (PR.md 3) |
| Ranges | `path:N-M` (and `N-M, P` lists) count when any cited line overlaps a location | Start line only: the bigin-phish run cites ranges everywhere (`middleware.go:129-131`) and would score low for the citation style, not the finding |
| Story citations | Own line, ID-linked Sources lines, and unlinked Sources lines (credited to each `[code]` criterion of that story) | ID-linked only: the story writer is not told to prefix citations with IDs, so real runs would score near 0 |
| Overlapping gold locations | Literal rule: one citation can find several rules (G-17/G-23 at `invoices_controller.rb:6`, G-10/G-15 at `invoice_issuer.rb:22`, G-07/G-13 at `invoices_controller.rb:25`) | 2.x's one-card-one-rule pick: needs kinds, which rspec has no equivalent for |
| 2.x extras | Dropped: kinds, near misses, precision, `--record`/JSON | PR.md's matching rule replaces them; the CHANGELOG records before-and-after numbers |
| Gold count | 33 rules (PR.md says 31; G-32 and G-33 were added after it was written) | — |

## Out of scope

- A live baseline run of discovery on the fixture (needs subagents; the first recorded run is follow-up work).
- Any change to discovery, the story writer or `check_spec.py`.

## Review

**What fired:** Code, because `## Public Surface` adds the `rules_recall.py` command. Risk is low, so it ran without asking. Security and UI did not fire.
**What ran:** the built-in `code-review high --max-findings all`, three rounds. Reports are in `.sdlc/.work/findings/2026-11-09-m-rules-recall/code-reviewer-r{1,2,3}.md`.

| Round | Verdict | Findings and what happened |
|---|---|---|
| 1 | FAIL: F1 F2 F4 F5 F6 F7 F10 (bugs, medium/low) | All fixed test-first. Numeric values had matched inside other numbers and IDs. Strays were listed once per criterion. Prose numbers after a comma were read as cited lines. Backslash, en-dash, `#L` and reversed citation forms were mishandled. Unknown arguments were ignored. Not bugs: F3 (strict uses the criterion's text, as PR.md defines it), F8 (research files not scored, as PR.md's rule says), F9 (one test, per the brief), F11 and F12 (cleanups). |
| 2 | FAIL: **R1 high** | The round-1 dash normalisation read `path:43 — 5 minutes` as the range 5–43 and credited 7 rules that were never cited, which breaks AC-001. Mediums R2–R6: a comma continuation still read prose as lines, `25.00` no longer matched `25`, `9%` matched inside `19%`, NFR-10's digits counted as values, and a reversed range was widened. Stopped at the round cap and asked. **User decision** (Tam Mai, via the coordinator): one fix round with a stricter design and one round-3 closing check, with no round 4. The design: a citation is only an exact token `path:N` or `path:N-M` (no spaces, start ≤ end), and a numeric value matches a whole number token by value, with `%` as part of the value, after every `ABC-12` ID is removed. Recorded in the state file's Gate log and Deviations. R1–R8 and R10 were fixed test-first, one test case per class. |
| 3 | PASS | Every round-2 class is gone. Fixed now, test-first, and closed by `verify.py`: T4 (`25,00` still yielded 0), T7 (line numbers from malformed citations counted as values), T10 (the gold header and README still described substring matching). T9: the Decisions row "Ranges" above still says comma lists count; the user's decision supersedes it (see the Deviations). Everything else in round 3 under-counts by design and is a ticket. |

**Tickets** (not bugs in this change, or under-counts the user's strict design accepts):
- A citation by bare file name (`line_item.rb:5-10`) never matches.
- Score `research/*.md` as a separate number, since discovery records `[code]` facts there.
- Read `#L` anchors, backslash paths, comma lists, Ruby ranges `1..10_000`, glued units (`3rd`, `5m`), `.09`, a trailing `path:15:`, and other glued separators (U+2212, `~`).
- `0%` against G-16's `0`: add `0%` to the gold group.
- Narrow `ANY_ID` so it stops stripping `net-30` and `HTTP-402`.
- Use `contracts.SPEC_ID` instead of `CRIT_ID`.
- Call `stdout.reconfigure` before the ERROR prints.
- Cleanups: one number grammar instead of two; read each story once; cache number tokens; reuse the section helper.
- A first recorded baseline run of discovery on the fixture.

**Drift:** recorded in Deviations: the red-step run command, the internal function names, and the redesign.
**Manual checks:**
- AC-006: `diff -r` shows `reference-src/` identical to product-rebuild's `docs/rspec-pr/rules-recall/reference-src`, and `gold.yaml` identical from `fixture:` down, with only the header rewritten.
- AC-007: `plugin.json` and `marketplace.json` both say 0.11.1, and the CHANGELOG has a `[0.11.1] - 2026-11-09` entry crediting MIGRATION-3.md row 9.

**Also:** `.sdlc/state/2026-11-08-l-rspec-criteria-ids.md` was set `Status: done` with `state.py set`, because it shipped as v0.11.0.
**Lessons filed:** `docs/sdlc/recurring-defects.md` (new).
