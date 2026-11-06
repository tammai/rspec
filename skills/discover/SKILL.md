---
name: discover
description: >
  This skill should be used when the user runs /rspec:discover or asks to explore,
  map or research the modules, screens and flows of the product being reverse-specced.
  Splits the product into modules and runs one module-explorer subagent per module in
  parallel, then merges results into <spec>/screens.md.
metadata:
  version: "0.9.3"
---

# /rspec:discover

Requires `<spec>/rspec.json` with stage `init` or later. Read `${CLAUDE_PLUGIN_ROOT}/references/discovery-checklist.md` first.

## 1. Build the module map (main session)
- Modernize track, or `code: true` (open-source product): build the map from the code (top-level packages, route groups, domain folders, database schemas) and the product's own docs, then the rest of this step as written. Give each subagent `track`, `code` and the source repo paths.
- If `modules` is set in the autopilot rules file (or the user lists modules), use that list as is.
- Otherwise anchor the split on the product's own top-level navigation: the sections of its main sidebar or menu and of its settings, as the help center's top-level navigation shows them. One module per top-level area; merge areas with only a few features into their nearest neighbour and split none unless it would hold more than about 30 features. Aim for 6–10 modules. Use the features page, the pricing page and the last 12 months of changelog only to place features inside that split, not to invent new modules. Two runs on the same product should get the same modules.
- Record the evidence for each module in its `sources` (the navigation page or help-center section it maps to).
- Give each module a 2–4 letter uppercase `code` (WS, TEAM, ISS, VIEW, PLAN, NOTI, INT, SET).
- Write them to `<spec>/rspec.json` → `modules: [{"code","name","scope","sources":[urls]}]`.
- Show the list to the user in a few lines and continue unless they object. Merge or split modules on request.

## 2. Explore modules in parallel
- Launch one `rspec:module-explorer` subagent per module **in a single message**. If there are more than 8 modules, launch in batches of 8.
- Give each subagent: product name, module code/name/scope, the module's source URLs, the global sources from rspec.json, `lang`, the output path `<spec>/research/<code lowercased>-<slug>.md`, and the absolute path of `${CLAUDE_PLUGIN_ROOT}` so it can read the templates and references.
- On resume, keep the existing module map and launch subagents only for the pending module codes; build `screens.md` once all research files exist.
- Tell each subagent which neighbouring modules exist so it does not document their features (it may list cross-module dependencies).

## 3. Merge (main session)
- Read every research file. Check each has Screens, Features observed, Sources. Re-run a single `rspec:module-explorer` subagent for any module that came back thin.
- Write `<spec>/screens.md` from `${CLAUDE_PLUGIN_ROOT}/templates/screens.md`: a sitemap grouped by area, global overlays, and 3–6 main end-to-end flows that cross modules.
- Collect all open questions into a short list in the reply.
- Set `stage` to `discovered`, update `updated`, add a line to `<changelog>`.
- Reply: modules explored, number of candidate features per module, notable recent additions, and next step `/rspec:features`.
