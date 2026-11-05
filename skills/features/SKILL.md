---
name: features
description: >
  This skill should be used when the user runs /rspec:features or asks to build the
  feature list, feature inventory or MVP scope of the product being reverse-specced.
  Compiles <spec>/features.md with IDs and MVP/Later/Drop priorities and stops for user approval.
metadata:
  version: "0.6.0"
---

# /rspec:features

Requires stage `discovered` or later. Read `${CLAUDE_PLUGIN_ROOT}/references/prioritization.md` and `writing-rules.md`.

1. Read `<spec>/rspec.json` (goal, focus) and every file in `<spec>/research/`.
2. Build the table in `<spec>/features.md` (template: `${CLAUDE_PLUGIN_ROOT}/templates/features.md`):
   - Keep the proposed IDs from research files (`F-<CODE>-NN`); renumber only to remove gaps or duplicates inside a module.
   - Merge duplicates found across modules into the module that owns the behaviour.
   - One-line behaviour in own words. Priority MVP / Later / Drop with a reason where required.
   - Order rows by module, then by dependency (foundations first).
3. Sanity-check the MVP: the core loop works end to end, every MVP dependency is also MVP, focus areas are covered, size is roughly ≤ 25 features.
4. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .` and fix errors.
5. **Approval gate.** Present to the user: count per module and priority, the full MVP list (ID + name), and the 3–5 most debatable calls. Ask them to approve or adjust. Do not proceed and do not change the stage until they explicitly approve.
6. After approval, apply any adjustments, set `stage` to `features-approved`, update `<spec>/README.md` scope section, add a line to `<changelog>`, and point to `/rspec:stories`.
