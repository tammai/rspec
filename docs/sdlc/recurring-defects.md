# Recurring defects

One line per defect: what it looks like, then the severity.

- A parser fix that normalises the whole line (rewriting dashes, separators or anchors before matching) turns nearby prose into structure, such as `path:43 — 5 minutes` read as the range 5–43; match the exact token instead. High (2026-11-09-m-rules-recall R1).
- A registry check that uses a hand-edited value (an `id` put in a set, a file read as UTF-8) before checking its type or encoding crashes with a traceback instead of an error line; check type and decoding first, on every value. High (2026-11-11-l-tracked-unknowns H2, H3).
- A cap or redaction applied to one runner's output path only (UI cut to 300 characters, HTTP messages written whole), so the committed log still holds whatever the reference echoed; apply it where every runner's result is logged. High (2026-11-15-m-verify-cost CR-1).
- A selection mode that skips a safety filter the default mode applies (`--plan --only` listing criteria the holdout hid), so naming an ID reopens what the filter closed; apply the filter before branching on the mode. High (2026-11-15-m-verify-cost CR-5).
- A check that a feature ID exists looks at the story files instead of features.md, so a Drop or out-of-scope feature (no story) reads as missing; features exist in features.md. High (2026-11-11-l-tracked-unknowns H1).
- A read-only check mode for a gate that hashes a generated file passes when the file is stale, or compares parsed content when the gate hashes bytes (a CRLF checkout parses equal), so the gate accepts a file the writer would change; fail when the bytes on disk differ from what the writer would write. High (2026-11-17-m-lock-lf-readonly CR-3).
- A second URL or setting read from an environment that an earlier step already rewrote (the adapter's URL read from env after `ACCEPT_BASE_URL` was set to the reference's), so a config naming the rewritten variable silently gets the wrong target; read every configured variable from the untouched `os.environ`, and refuse names that collide. High (2026-11-16-m-reference-adapter H-1).
