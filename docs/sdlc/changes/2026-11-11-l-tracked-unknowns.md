# Tracked unknowns: unknowns.yaml, and no level above 0 while a criterion's question is open

## Why

**Request (verbatim):** "go ahead" (choosing "Item 1: unknowns file (rspec)" from the remaining work: "unknowns.yaml with U-IDs, the criteria each blocks and the probe that would settle it; check_spec.py keeps a blocked criterion at level 0"). It is item 1 of what rspec could learn from morluto/rea: REA's `record_unknown` gives each unresolved question an identity, the evidence for and against it, the authority still needed and a recommended probe, and its completion check stays `unknown` while a required question is open.

Today rspec's unknowns are prose. A module explorer writes them under its research file's `## Open questions`; a story writer writes `Open: domain:` / `Open: departure:` / `Open: …` lines under the story's `## Open questions`; writing-rules says "write `unknown` and add it to the module's open questions". No script reads any of it, and `/rspec:stories` step 3 empties every story's `## Open questions` to `- none` after handling domain rules and departures, so a question nobody could answer leaves no trace. The criterion it affects is written anyway, usually `[inferred]`, and can still reach level 1 or 2. A builder reading the lock cannot tell "we checked" from "we never found out".

This change gives an unanswered question a record that outlives the story pass, links it to the criteria whose expected result depends on it, says what would settle it, and makes the levels honest about it. It serves whoever builds from the spec (the lock and the build plan tell them which criteria rest on an open question) and whoever maintains the spec (the questions to chase are one list).

**The user's words:** None asked: run under the sdlc orchestrator, every open point below is settled with a recommended answer (`[recommended]`) for the approval.

## Questions settled for the approval

1. **Where do unknowns live?** `<spec>/unknowns.yaml`, a list like `departures.yaml` (C5): one registry, IDs `U-<nnn>` never reused. `[recommended]` (approach A below)
2. **Who writes it?** Not the subagents. Story writers write `Open: unknown: <question> — probe: <what would settle it>` lines and name the criteria they affect in their reply; `/rspec:stories` step 3 moves every such line it cannot answer from the sources into `unknowns.yaml`, exactly as it handles `Open: departure:`. The audit adds one for an Important UNSUPPORTED or DECISION finding it cannot settle. `[recommended]` (mirrors "writers never write departures.yaml")
3. **What does an open unknown do to a criterion?** Caps it at level 0 in `criteria.lock.json`, level 1 and level 2 alike: the expected result itself is in question, and a test recorded from it proves only that the reference did what the guess said. Resolving the unknown lifts the cap on the next `check_spec.py` run. `[recommended]`
4. **Statuses.** `open`, `resolved` (with `resolution` and `evidence`: the source that answers it) and `accepted` (the user decided to build on the criterion as written, a known risk, with `decided_by`). `accepted` lifts the cap like `resolved`; it records that nobody found out, which the build plan shows. `[recommended]`
5. **When does an open unknown block?** A warning until handoff; from handoff on, an `open` unknown that blocks an in-scope criterion is an error (resolve it or accept it), the same rule as a `proposed` departure. Since `/rspec:handoff` starts while the stage is still `tech`, its first step is the real gate: it runs `check_spec.py` and settles every `open … U-<nnn>` warning in scope (resolve, or ask the user to accept) before anything else; the error from stage `handoff` on is the backstop that keeps a later edit from reopening one silently. Under autopilot, the stories and audit steps park each new unknown under `## Parked` in `autopilot-log.md`, and handoff stops on them like any parked decision. `[recommended]`
8. **Can a story reader see the question?** Yes: step 3 replaces each moved `Open: unknown:` line with `- U-<nnn>: <question>` in the story's `## Open questions` (instead of emptying it), and keeps it there while the unknown is open; resolving or accepting it removes the line. `[recommended]`
9. **Scope.** The level cap applies to every criterion an `open` unknown names, in scope or not (the lock covers every story). The handoff error applies only when one of its criteria or features is in scope (`rspec_lib.in_scope`): an unknown about a Drop or out-of-scope Later feature doesn't block a build that leaves it out. `[recommended]`
6. **Revision history and supporting/contradicting evidence lists (REA)?** Not kept: git history is the revision record, and one `evidence` list on resolution is enough for a spec. `[recommended]`
7. **Research-file questions?** Stay prose; they predate criteria, and step 3 is where a question meets the criteria it blocks. `[recommended]`

## Decisions

| Decision | Ruled out | Why |
|---|---|---|
| **A. A registry file, `<spec>/unknowns.yaml`** (chosen) | | Mirrors `departures.yaml`, the spec's existing registry: one list, stable IDs, links to criteria, checked by `check_spec.py`. A question that spans several stories exists once |
| | **B. Structured lines in each story's `## Open questions`**, parsed by `check_spec.py` | No new file, but a question shared by stories is duplicated and drifts, and step 3 empties that section today; keeping it would change the story format every existing spec uses (constitution VI) |
| | **C. A field in `criteria.lock.json`** (e.g. `blocked_by`) | C3 is the vendored contract (`contracts/v1/`): a new field is a contracts change in product-rebuild and three re-vendors. The level cap alone needs no new field: C3 lets a producer be stricter |
| The schema check lives in `check_spec.py` (stdlib, `contracts.parse_yaml`), not in `contracts/v1/` | A C8 contract | rspec-only file; nothing outside rspec reads it |
| No migration script | A script converting old `Open:` lines | A spec without `unknowns.yaml` has no unknowns and keeps working; old prose questions were already emptied by step 3 |

**Proposals not asked for:** None.

## Design

**`<spec>/unknowns.yaml`** (absent = no unknowns). A YAML list; each entry:

```yaml
- id: U-001                       # U-<nnn>, numbered on from the highest, never reused
  question: Does archiving a team also archive its issues?
  criteria: [F-TEAM-03.AC2]       # criteria whose expected result depends on the answer (may be empty)
  features: [F-TEAM-03]           # optional; at least one of criteria / features
  probe: Archive a seeded team on the reference and read its issues   # what would settle it
  status: open                    # open | resolved | accepted
  raised: stories 2026-11-11      # step and date
  # resolved: resolution (one line) and evidence (list of URLs or path:line), both required
  # accepted: decided_by "<user>, <step> <date>", required
```

**`check_spec.py`** (one new function beside `check_departures`, called before `write_lock`):
- Errors: not a list; an entry not a mapping; a missing or malformed `id`, a duplicate `id`; missing `question`, `probe` or `status`; an unknown `status`; neither `criteria` nor `features`; an `open` entry naming a criterion or feature ID the spec doesn't have (a struck criterion counts as unknown to the spec); `resolved` without `resolution` and a non-empty `evidence`; `accepted` without `decided_by`. A `resolved` or `accepted` entry naming a missing or struck ID is only a warning: history, not a defect (an amend may strike the criterion it settled).
- From handoff on (the same `si >= 5` test `check_departures` uses): an `open` entry that names an in-scope criterion or feature is an error; before it, a warning naming the entry.
- `write_lock` takes the set of criteria named by `open` entries (directly, or through a listed feature: every active criterion of that feature) and writes them at level 0, whatever the audit or verify levels say, with one warning per capped criterion that names the unknown (`F-TEAM-03.AC2: level 1 capped to 0 by open U-001`). The audit and verify level files are untouched, so resolving the unknown restores the level on the next run.
- Every `U-<nnn>` mentioned in a story or features.md must exist in `unknowns.yaml` (error), as for `D-` links.

**Prompts and skills:**
- `agents/story-writer.md`: an unanswerable question that changes a criterion's expected result → `Open: unknown: <question> — probe: <what would settle it>` under `## Open questions`; write the criterion as the best reading, tagged `[inferred]`; name the question and the criteria it affects in the reply.
- `skills/stories/SKILL.md` step 3: answer each `Open: unknown:` from the sources if possible (fix the criterion); move the rest into `unknowns.yaml` (`status: open`, `raised: stories <date>`; autopilot: also park it) and replace the line with `- U-<nnn>: <question>`, which stays when the rest of `## Open questions` is emptied.
- `skills/handoff/SKILL.md` first step: run `check_spec.py`; every `open` unknown it warns about in scope is resolved or put to the user to accept (AskUserQuestion; autopilot: stop on it as parked) before the build plan is written.
- `skills/audit/SKILL.md` step 3: an Important UNSUPPORTED or DECISION finding that neither the sources nor the user settle now becomes an `open` unknown on that criterion (autopilot: parked).
- `skills/handoff/SKILL.md` step 3 and `templates/build-plan.md`: each slice lists its `accepted` unknowns as known risks (ID and question); handoff refuses to start while `check_spec.py` reports an `open` one in scope.
- `skills/amend/SKILL.md`: an amend that settles an unknown sets it `resolved` with the evidence.
- `references/writing-rules.md`: the "write `unknown`" rule points at `Open: unknown:`.
- README "What you get" lists `unknowns.yaml`; CHANGELOG `[Unreleased]`.

## Goals, non-goals, anti-goals

- **Goals:** an unanswered question survives the story pass with its probe; the lock never shows a criterion above level 0 while its expected result is an open question; handoff can't pass over an open one silently.
- **Non-goals:** recording research-file questions; REA's revision numbers and per-revision evidence lists; a contracts change; running probes automatically.
- **Anti-goals:** the registry filling with questions that don't change any criterion (an entry needs a criterion or feature); specs written before this change failing `check_spec.py`.

## Calls made, and what's left to the builder

- Calls: the nine `[recommended]` answers above; `accepted` lifts the cap (the risk is shown in the build plan instead). A builder can tell capped from never-checked: at handoff no `open` unknown remains in scope, so every in-scope criterion at level 0 is simply unaudited or unverified, and every risk taken knowingly is an `accepted` unknown listed in its slice. (Answers 5, 8 and 9 came from the builder check, along with the open-only existence error.)
- Left to the builder: message wording; where in `check_spec.py` the function sits; the test fixtures.

## Acceptance criteria

- **AC-001** Given a criterion at level 1 in the audit levels and level 2 in the verify levels, and an `open` unknown naming it (directly, or through its feature), when `check_spec.py` runs, then the lock has it at level 0 and a warning names the unknown; after the unknown is set `resolved` (or `accepted`), the next run restores its level.
- **AC-002** Given `unknowns.yaml` with a duplicate ID, an unknown status, a missing `probe`, an `open` entry naming an unknown criterion ID, a `resolved` entry without evidence, or an `accepted` entry without `decided_by`, when `check_spec.py` runs, then it exits non-zero with one error naming each; a `resolved` entry naming a struck criterion is a warning only.
- **AC-003** Given an `open` unknown naming an in-scope criterion, when `check_spec.py` runs before handoff, then it warns; at stage handoff or later, then it errors; an `open` unknown naming only an out-of-scope feature never errors.
- **AC-004** Given a story that mentions `U-007` and no such entry, when `check_spec.py` runs, then it errors naming the story and the ID.
- **AC-006** The story writer, the stories, audit, amend and handoff skills, the build-plan template, writing-rules and the README describe the flow in the Design above.

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | tests/test_unknowns.py › test_open_unknown_caps_level_until_resolved | `python3 -m unittest discover tests -k test_open_unknown_caps_level_until_resolved` |
| AC-002 | tests/test_unknowns.py › test_malformed_entries_are_errors | `python3 -m unittest discover tests -k test_malformed_entries_are_errors` |
| AC-003 | tests/test_unknowns.py › test_open_unknown_blocks_from_handoff | `python3 -m unittest discover tests -k test_open_unknown_blocks_from_handoff` |
| AC-004 | tests/test_unknowns.py › test_unknown_link_must_exist | `python3 -m unittest discover tests -k test_unknown_link_must_exist` |
| AC-006 | manual | Prompt, skill and template wording; checked by reading each file against the Design |

## Must never break

- A spec without `unknowns.yaml` checks and locks exactly as before (tests/test_unknowns.py › test_no_registry_changes_nothing).
- Audit and verify level files are never rewritten by `check_spec.py`; a cap is applied only in the lock.
- `criteria.lock.json` keeps the C3 shape (no new fields) and passes `contracts.check_lock`.

## Failure modes

- Malformed YAML or wrong types in `unknowns.yaml` (hand-edited file) → AC-002 (an error, never a traceback).
- An unknown naming a criterion later struck or renumbered → AC-002 (unknown criterion ID).
- A spec from before this change → must never break, first line.

## Out of scope

- Questions in research files; a probe runner; REA's revision history.
- sdlc spec questions (`$S question`) feeding `unknowns.yaml` through `/rspec:amend`: a natural follow-up, not this change.

## Review

- **Recommended and chosen:** code, because the track is L; chosen by the trigger list (self-chosen, L). Security, UI and advisor did not fire (low risk, no sensitive or UI paths).
- **Verdicts:** code-reviewer → `.sdlc/.work/findings/2026-11-11-l-tracked-unknowns/code-reviewer-r1.md` → FAIL — H1, H2, H3, H4, H5, M1; `code-reviewer-r2.md` → PASS.
- **Fixed:** H1 named features checked against story files, so a Drop or out-of-scope Later feature errored: now against features.md (`test_named_features_are_checked_against_features_md_and_scope`). H2 a non-string `id` crashed with a TypeError: an ID is recorded only once it matches `U-<nnn>`; H3 invalid UTF-8 traced back: caught as an error (both in `test_registry_shape_errors_never_trace`). H4 the level 2 cap and the untouched level files had no test (`test_open_unknown_caps_verified_level_2_and_keeps_level_files`). H5 handoff step 0 could leave an unknown open and its story line behind: every path now ends resolved or accepted and removes the line. M1 untested behaviours (struck criterion, scope, shape errors): `test_struck_criterion_errors_only_while_open` and the shape cases. In passing: M2 U- links are read only from `- U-<nnn>:` lines in `## Open questions` (`test_only_open_question_lines_are_links`), M3 unknown keys are errors, F1 a missing status says so, F2 the audit sets `raised`, F3/L2 the build-plan risk line has no nested placeholders or feature IDs, L3 handoff step 0 runs on resume. After round 2: L-a four more shape cases tested, L-b handoff step 0 acts on the warning or the error form, L-c the story template's Open questions placeholder names the new lines.
- **Tickets:** r1 H3's twin (departures.yaml traces back on invalid UTF-8, code this change didn't touch), r1 L1 (a level kept only in the previous lock is lost after a cap), r1 L4 (link scan duplicates check_departures' shape), r2 M-a (at stage handoff an open unknown is an error, so the lock isn't rewritten and keeps the earlier level until the check is clean, as for every check error): all in `docs/sdlc/todo.md`.
- **Drift and manual checks:** Deviations: AC-005 became a must-never-break line (it couldn't fail first); `check_unknowns` added and `write_lock` given a `capped` argument; U- links only from Open questions lines (M2), unknown keys are errors and features checked against features.md (M3, H1). AC-006 checked by the reviewer in both rounds and by me reading each file against the Design.
- **Lessons filed:** two lines in `docs/sdlc/recurring-defects.md`.
