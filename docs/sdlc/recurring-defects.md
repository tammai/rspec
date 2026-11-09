# Recurring defects

One line per defect: what it looks like, then the severity.

- A parser fix that normalises the whole line (rewriting dashes, separators or anchors before matching) turns nearby prose into structure, such as `path:43 — 5 minutes` read as the range 5–43; match the exact token instead. High (2026-11-09-m-rules-recall R1).
