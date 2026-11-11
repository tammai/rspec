# Todo

## Open


- [ ] verify_report.py counts a hidden criterion at level 2 even after its text changes (the holdout split moves its runs away, so the current-text rule cannot be checked); decide whether a changed hidden criterion should drop to level 0 — review M3 of the S-37 fix, scripts/verify_report.py (2026-11-09)
- [ ] verify_report.py writes hidden manifest entries after the open ones, so the first re-run reorders a mixed manifest (entries unchanged, the committed file shows a diff) — review L1 of the S-37 fix, scripts/verify_report.py (2026-11-09)
- [ ] verify_report.py silently leaves out a new open test recorded for a criterion that already has a hidden entry; warn or decide which wins — review L2 of the S-37 fix, scripts/verify_report.py (2026-11-09)
- [ ] Add one test that a damaged acceptance/manifest.json makes verify_report.py exit non-zero with the restore error instead of a traceback — review round 2 M4 of the S-37 fix; the brief allowed one test, tests/test_verify.py (2026-11-09)
- [ ] verify_report.py's damaged-manifest error should also offer "or delete it to rebuild it from the run log (hidden entries are lost)", for a manifest never committed — review round 2 L3 of the S-37 fix (2026-11-09)

## Done

- [x] departures.yaml read in check_departures traces back on invalid UTF-8 (unknowns.yaml now catches it); catch UnicodeDecodeError the same way — review r1 H3 of 2026-11-11-l-tracked-unknowns, scripts/check_spec.py (2026-11-11) → fixed: caught like unknowns.yaml (2026-11-11-m-unknowns-review-tickets)
- [x] A criterion level kept only in the previous lock (no audit or verify level file behind it) is lost after an open unknown caps it; decide whether the cap should leave the stored level recoverable — review r1 L1 of 2026-11-11-l-tracked-unknowns, scripts/check_spec.py write_lock (2026-11-11) → closed without change: levels are rebuilt from audit/ and verify/levels.json, which the cap never touches; a level with no file behind it is re-earned by rerunning the audit or verify (2026-11-11-m-unknowns-review-tickets)
- [x] check_unknowns' story link scan and check_departures' D- link scan could share one helper — review r1 L4 of 2026-11-11-l-tracked-unknowns, scripts/check_spec.py (2026-11-11) → fixed: report_unlisted is shared (2026-11-11-m-unknowns-review-tickets)
- [x] At stage handoff an open in-scope unknown is an error, so the lock isn't rewritten and keeps the criterion's earlier level until the check is clean; decide whether to write the capped lock even on that error — review r2 M-a of 2026-11-11-l-tracked-unknowns, scripts/check_spec.py (2026-11-11) → fixed: the capped lock is written when the open unknown is the only error (2026-11-11-m-unknowns-review-tickets)
