# Todo

## Open

- [ ] verify_report.py counts a hidden criterion at level 2 even after its text changes (the holdout split moves its runs away, so the current-text rule cannot be checked); decide whether a changed hidden criterion should drop to level 0 — review M3 of the S-37 fix, scripts/verify_report.py (2026-11-09)
- [ ] verify_report.py writes hidden manifest entries after the open ones, so the first re-run reorders a mixed manifest (entries unchanged, the committed file shows a diff) — review L1 of the S-37 fix, scripts/verify_report.py (2026-11-09)
- [ ] verify_report.py silently leaves out a new open test recorded for a criterion that already has a hidden entry; warn or decide which wins — review L2 of the S-37 fix, scripts/verify_report.py (2026-11-09)
- [ ] Add one test that a damaged acceptance/manifest.json makes verify_report.py exit non-zero with the restore error instead of a traceback — review round 2 M4 of the S-37 fix; the brief allowed one test, tests/test_verify.py (2026-11-09)
- [ ] verify_report.py's damaged-manifest error should also offer "or delete it to rebuild it from the run log (hidden entries are lost)", for a manifest never committed — review round 2 L3 of the S-37 fix (2026-11-09)
