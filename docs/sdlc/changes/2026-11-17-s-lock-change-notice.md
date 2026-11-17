# check_spec says when it changes the criteria lock's content

## Why

product-rebuild reported that on the CRM workbench, a plain `/rspec:check` with 0.15.0 rewrote `criteria.lock.json`'s content: contracts 1.3.0→1.3.1, `generated`, and `departures` [] → ["D-051"]/["D-052"]. Gate 4 had locked the lock, so product-rebuild's validate failed with "locked artifact modified", and the CRM session had to work out by itself that it needed a relock. Their suggestion, which the user accepted: "when check_spec.py changes the content of a lock that a gate has locked, or any time it changes more than line endings, it should say so … not silently modify a locked file."

## Decisions

| Decision | Chosen | Ruled out |
|---|---|---|
| When to say it | Every write that changes an existing lock's parsed content | Detecting product-rebuild's gate locks: rspec doesn't know the gate's files, and the advice applies to any committed lock |
| How | One WARN naming the changed fields (the first 3 criterion IDs for each field) | An ERROR: check did the right thing, and a spec without a gate must still pass |

## Acceptance criteria

- **AC-001** When `check_spec.py` rewrites an existing lock whose content changed, it prints one WARN starting `criteria.lock.json updated:` that names what changed (e.g. `contracts version`, `departures (F-ISS-01.AC1)`) and says to reopen and relock it if a gate locked it. A rewrite that only changes line endings prints no such line.

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | tests/test_criteria_ids.py › test_content_change_to_lock_is_announced | `python3 -m unittest discover tests -k test_content_change_to_lock_is_announced` |

## Must never break

- The first lock write (no lock yet) and an unchanged lock print no `updated` line.
- Existing per-criterion warnings (`text changed since the last lock`, capped levels) stay as they are.

## Out of scope

- Naming what differs in `--no-lock`'s error.

## Review

No review ran: no trigger fired.
