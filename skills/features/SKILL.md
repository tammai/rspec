---
name: features
description: >
  This skill should be used when the user runs /rspec:features or asks to build the
  feature list, feature inventory or MVP scope of the product being reverse-specced.
  Compiles <spec>/features.md with IDs and MVP/Later/Drop priorities and stops for user approval.
  Also triages features later ("bring back the AI features", "move F-INT-23 to Later",
  "/rspec:features triage"): changes priorities and specs only what changed, without rerunning the pipeline.
argument-hint: "[triage F-ID=MVP|Later|Drop ...]"
metadata:
  version: "0.9.2"
---

# /rspec:features

Requires stage `discovered` or later. Read `${CLAUDE_PLUGIN_ROOT}/references/prioritization.md` and `writing-rules.md`.

1. Read `<spec>/rspec.json` (goal, focus) and every file in `<spec>/research/`.
2. Build the table in `<spec>/features.md` (template: `${CLAUDE_PLUGIN_ROOT}/templates/features.md`):
   - Keep the proposed IDs from research files (`F-<CODE>-NN`); renumber only to remove gaps or duplicates inside a module. Put the research file's own ID in the `Research ID` column (blank if unchanged), so story writers can find the feature in the research without matching by name.
   - Merge duplicates found across modules into the module that owns the behaviour.
   - One-line behaviour in own words, at most about 20 words; details belong in the story. Priority MVP / Later / Drop with a reason where required.
   - Order rows by module, then by dependency (foundations first).
3. Modernize track: MVP means parity at cutover, Drop means retire (see prioritization.md); list every retired feature that still has users in the approval message as a decision for the user. Otherwise:
   With `scope` `full` every MVP and Later feature gets a story and contracts; MVP decides only what is built first (release 1). Sanity-check the MVP: the core loop works end to end, every MVP dependency is also MVP, focus areas are covered, size is roughly ≤ 25 features.
4. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .` and fix errors.
5. **Approval gate.** Present to the user: count per module and priority, the full MVP list (ID + name), and the 3–5 most debatable calls. Ask them to approve or adjust. Do not proceed and do not change the stage until they explicitly approve. If `autopilot.enabled` is true in `rspec.json`, do not ask: apply the user's rule in `autopilot.rules` (see the Autopilot section of the pipeline skill), record the decision in `<spec>/autopilot-log.md`, and park anything the rule does not cover.
6. After approval, apply any adjustments, set `stage` to `features-approved`, update `<spec>/README.md` scope section, add a line to `<changelog>`, and point to `/rspec:stories`.

## Triage (after approval)

`/rspec:features triage F-INT-23=Later F-ISS-29=MVP …`, a request in words, or `next` = `triage` in the progress output (someone edited a priority in features.md by hand; `pending` lists those IDs). It changes only the features named and leaves every other story, contract, ADR and slice alone. Without arguments, list the Drop rows with their reasons and ask which to bring back.

1. **Validate.** Promoting to MVP: every Later feature the story depends on must also become MVP; list them and ask (autopilot: promote them too and log it). Demoting from MVP, or to Drop: every feature in scope that depends on it must move too or drop the dependency; list them and ask (autopilot: park it). A feature whose slice sdlc has already started (`build.slices`) or whose story is `done` cannot go to Drop; say so.
2. **features.md.** Update the priority and reason of each row (a Drop keeps a one-line reason). Add a line to `<changelog>`: `Triage: F-… Drop → Later, …`.
3. **Stories.** For features newly in scope without a story, run `rspec:story-writer` per module in batches of about 10, MVP first, as in step 2 of `rspec:stories`, with every story already written as the IDs they may depend on. After the last batch, run `scripts/merge_deps.py`. For a priority change of a feature that has a story, update `priority` in its frontmatter. Leave Drop stories in place; they are kept for a later triage.
4. **Contracts** (stage `tech` or later). Run `rspec:tech-analyst` with `area` `api` and `data-model` in **add mode** (`add: [IDs]`) in one message: they add operations, schemas and `x-features` for those IDs only and keep every existing one. Add NFR rows only if a new feature needs its own. No ADR changes unless a new feature needs a new decision; draft it as Proposed (the handoff gate applies).
5. **Build plan** (stage `handoff`). Remove Drop features from slices not yet started. Add features newly in scope: MVP ones into the first release whose slices are not started, else into a new slice right after the last started one; Later ones as a new release at the end (or into a not-started release of the same area), in dependency order, keeping the slice limits. Never change a started slice. Under sdlc, say that the change reaches sdlc through the next slice it starts.
6. Run `check_spec.py` and `progress.py`; fix errors until `next` is no longer `triage`. Reply with what moved, the new stories and slices, and anything parked.
