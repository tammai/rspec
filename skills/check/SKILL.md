---
name: check
description: >
  This skill should be used when the user runs /rspec:check or asks to validate,
  lint or review the completeness of a reverse spec.
metadata:
  version: "0.8.1"
---

# /rspec:check

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .`.
2. Report the summary line, then errors and warnings grouped by file, in the user's language.
3. Beyond the script, spot-check five random story files for: testable criteria, confidence tags on facts, own wording (no pasted vendor text), and sources.
4. Offer to fix. Fix only what the user agrees to. Under autopilot (`autopilot.enabled` in `rspec.json`), do not ask: fix errors once, leave warnings, and add anything you could not fix under `## Parked` in `<spec>/autopilot-log.md`.
