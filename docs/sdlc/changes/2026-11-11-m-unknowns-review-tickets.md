# Unknowns review tickets: departures.yaml encoding, capped lock at handoff, one link scanner

## Why

**Request (verbatim):** "- rspec docs/sdlc/todo.md: four small tickets from the item 1 review. One is that departures.yaml can crash on invalid UTF-8, the same problem now fixed for unknowns.yaml. […] do 2 items, drop 2 other" (the four tickets that 2026-11-11-l-tracked-unknowns' review left in `docs/sdlc/todo.md`).

Closes those four tickets: two are bugs (a traceback, and a stale lock that can show a capped criterion above level 0), one is a cleanup, one is closed with its reason.

## Decisions

| Decision | Ruled out | Why |
|---|---|---|
| At any stage, the lock is still written when every error comes from an open unknown blocking handoff; any other error still holds it | Writing the lock despite any error | The cap is exactly what such an error is about; other errors can mean the stories themselves can't be read, so the lock stays as it was |
| Ticket "a level kept only in the previous lock is lost after a cap": closed, not changed | Storing the pre-cap level | The lock carries no field for it (C3), and levels are rebuilt from `audit/levels.json` and `verify/levels.json`, which the cap never touches; a level with no file behind it is re-earned by rerunning the audit or verify |
| One helper scans a story section for registry links, used by both checks | Keeping two scanners | Ticket L4; the `D-` scan keeps its current reach (every story and features.md) |

## Acceptance criteria

- **AC-001** Given a `departures.yaml` with invalid UTF-8 bytes, when `check_spec.py` runs, then it reports `ERROR departures.yaml: …` and exits 1 with no traceback.
- **AC-002** Given a spec at stage `handoff` whose only error is an open unknown blocking an in-scope criterion that the lock had at level 1, when `check_spec.py` runs, then it exits 1 with that error and the lock now has the criterion at level 0.

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | tests/test_departures.py › test_invalid_utf8_is_an_error | `python3 -m unittest discover tests -k test_invalid_utf8_is_an_error` |
| AC-002 | tests/test_unknowns.py › test_handoff_error_still_writes_the_capped_lock | `python3 -m unittest discover tests -k test_handoff_error_still_writes_the_capped_lock` |

## Must never break

- Any error other than an open unknown at handoff still leaves `criteria.lock.json` untouched.
- `D-` and `U-` link checks report exactly what they did before (the existing departures and unknowns tests).

## Review

No review ran: low risk, no trigger fired; every AC red then green (verify.py).
