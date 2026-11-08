---
name: audit
description: >
  This skill should be used when the user runs /rspec:audit or asks to audit, fact-check or
  verify a reverse spec: are its facts true, does it cover what the product documents, does it
  contradict itself. Runs three auditor subagents in parallel (fact-checker, coverage-auditor,
  consistency-auditor), fixes the Important findings and lists the Minor ones. The pipeline runs
  it after tech, before handoff.
argument-hint: "[facts | coverage | consistency, optional; default all three]"
metadata:
  version: "0.9.7"
---

# /rspec:audit

Requires stage `tech` or later (coverage alone works from `discovered`). Reports go to `<spec>/audit/`. The audit rule: only Important findings change the spec; Minor findings are listed, not applied, unless the user asks.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit_sample.py .` to draw the fact-check sample: for each of `[docs]` `[api]` `[observed]` `[code]` `[inferred]`, `min(25, max(5, 20%))` criteria with a fixed seed (`<spec>/audit/sample.md` for the fact-checker, `sample.json` for the levels).
2. Launch **in a single message** (only the parts named in `$ARGUMENTS`, or on resume only those whose report is missing):
   - `rspec:fact-checker` with product, `<spec>`, the sample path, `sources` and `reference.run` from `rspec.json` and the plugin root;
   - `rspec:coverage-auditor` with mode `audit`, product, `<spec>`, `sources`, `focus` and the plugin root (it reuses `<spec>/audit/reference.md` from the features stage);
   - `rspec:consistency-auditor` with `<spec>`, `<contracts>`, `<decisions>` and the plugin root.
3. When they return, read each report's Important section and fix the spec, one finding at a time:
   - **Fact:** retag the criterion `[inferred]`, split it, or correct the value to what the source says; a deliberate difference goes under the story's `## Open questions` as `Open: departure: <what>` and is decided as in `/rspec:stories`' departures step (asked now, with the DECISIONs below). A DECISION on an `[inferred]` criterion goes to the user with the options the fact-checker named (AskUserQuestion, up to 4 per question); under autopilot park it under `## Parked` in `<spec>/autopilot-log.md`.
   - **Coverage:** a missing core or focus capability becomes a features.md row through `rspec:features` Triage (or a Drop row with a reason); never add a story without a row.
   - **Consistency:** make the files agree with `domain.md` and the accepted ADRs; when `domain.md` itself is wrong or silent, fix it first. When the right answer is a product decision, ask the user (autopilot: take the side `domain.md` or the accepted ADR supports; if neither does, park it under `## Parked` in `<spec>/autopilot-log.md`).
4. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit_sample.py . --levels` (it writes `<spec>/audit/levels.json`: sampled criteria confirmed by the fact-checker, and unsampled ones in a tag population whose sample has no CONTRADICTED, reach level 1; a criterion with its own finding does not), then `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .`, which writes those levels into `criteria.lock.json`; fix errors. A criterion edited afterwards drops back to level 0.
5. Write `<spec>/audit/summary.md`: the first line of each report, the `--levels` output line (level 1 count, copied, never computed by hand), the targets (fact accuracy at least 90% with 0 contradicted, coverage at least 90%, 0 Important contradictions left), what was fixed, what was parked, and the Minor counts. Add a line to `<changelog>`. Reply with the three scores, what you fixed and what is parked.
