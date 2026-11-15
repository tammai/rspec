# Recurring defects

One line per defect: what it looks like, then the severity.

- A parser fix that normalises the whole line (rewriting dashes, separators or anchors before matching) turns nearby prose into structure, such as `path:43 — 5 minutes` read as the range 5–43; match the exact token instead. High (2026-11-09-m-rules-recall R1).
- A registry check that uses a hand-edited value (an `id` put in a set, a file read as UTF-8) before checking its type or encoding crashes with a traceback instead of an error line; check type and decoding first, on every value. High (2026-11-11-l-tracked-unknowns H2, H3).
- A cap or redaction applied to one runner's output path only (UI cut to 300 characters, HTTP messages written whole), so the committed log still holds whatever the reference echoed; apply it where every runner's result is logged. High (2026-11-15-m-verify-cost CR-1).
- A selection mode that skips a safety filter the default mode applies (`--plan --only` listing criteria the holdout hid), so naming an ID reopens what the filter closed; apply the filter before branching on the mode. High (2026-11-15-m-verify-cost CR-5).
- A check that a feature ID exists looks at the story files instead of features.md, so a Drop or out-of-scope feature (no story) reads as missing; features exist in features.md. High (2026-11-11-l-tracked-unknowns H1).
