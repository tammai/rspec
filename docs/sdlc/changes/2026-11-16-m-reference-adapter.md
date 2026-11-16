# Verify through a reference adapter

## Why

> Item 6 of tammai/product-rebuild#9, approved design: product-rebuild `docs/specs/contract-shaped-tests/design.md` ("rspec (only takes an adapter URL)", points 5 and 6). Build order step 1.

A rebuild whose locked contract differs from the reference's API (the CRM: REST over Twenty's GraphQL) recorded tests the build can never pass. With an adapter (a pass-through service that serves the locked `openapi.json` and calls the reference), rspec records contract-shaped HTTP tests and proves them on the reference through it. The build later runs the same tests directly.

## Acceptance criteria

- **AC-001** (design 5) With `reference.run.adapter` set, `verify_run.py` runs an HTTP test with `ACCEPT_BASE_URL` set to the URL in the adapter's `base_url_env`, not the reference's.
- **AC-002** (design 6) With an adapter set, `verify_run.py` refuses an HTTP test when any request path in its steps or its seeds is not a path in `<contracts>/openapi.json`. It names the path and the file, and logs no run.
- **AC-003** With an adapter set, an adapter that doesn't answer, or a reference behind it that doesn't, stops the run as `not run` (`adapter unreachable: …` or `reference unreachable: …`), exit 3.
- **AC-004** `check_spec.py` and `verify_run.py` refuse, with one error line and no traceback, an `adapter` that isn't an object, has no `start`, or whose `base_url_env` isn't an `ACCEPT_*` variable, is `ACCEPT_BASE_URL` or is the reference's own.
- **AC-005** The verify skill, criterion-recorder and reference-seeder say how the adapter is started and checked, that HTTP tests and seeds use only contract operations, and that UI and mobile tests still run against the reference.

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | `tests/test_verify.py` › Verify.test_adapter_runs_http_tests_through_it | `python3 -m unittest discover -s tests -k test_adapter_runs_http_tests_through_it` |
| AC-002 | `tests/test_verify.py` › Verify.test_adapter_refuses_a_path_outside_the_contract | `python3 -m unittest discover -s tests -k test_adapter_refuses_a_path_outside_the_contract` |
| AC-003 | `tests/test_verify.py` › Verify.test_unreachable_adapter_or_reference_stops_as_not_run | `python3 -m unittest discover -s tests -k test_unreachable_adapter_or_reference_stops_as_not_run` |
| AC-004 | `tests/test_verify.py` › Verify.test_reference_run_rules, Verify.test_a_malformed_adapter_is_one_error_line | `python3 -m unittest discover -s tests -k test_reference_run_rules -k test_a_malformed_adapter_is_one_error_line` |
| AC-005 | manual | prompt text, checked against the design at Review |

## Must never break

- Without `reference.run.adapter`, `verify_run.py` behaves exactly as before: same URL, no path check.
- e2e and mobile tests always run against the reference's URL, adapter or not. The rebuild's pages aren't the reference's, so UI criteria keep a departure plus builder tests (the user's decision, 2026-11-16).

## Decisions

| Decision | Chosen | Ruled out |
|---|---|---|
| Where the adapter URL comes from | Its own `ACCEPT_*` variable (`adapter.base_url_env`), like the reference's | A literal URL in rspec.json: rspec.json is committed and the URL is per machine |
| Path check | Exact match of each request path (query string dropped) against openapi.json's path templates; `{param}` and a `{capture}` both match one segment | Matching method too: a test's method is the contract's to check at review, and the path alone already refuses a reference-native call |
| Seeds | Checked like test steps | Exempt: seeds run against the build at G6 too, so a reference-only reset or admin endpoint must be a contract operation (a spec question when it's missing) |

## Review

**What fired:** Code, because the change adds a config key (`reference.run.adapter`). Low risk, so it ran without asking. It ran `sdlc:code-reviewer` on opus at full depth.

**Round 1: FAIL** (`.sdlc/.work/findings/2026-11-16-m-reference-adapter/code-reviewer-r1.md`)
- **H-1 (high).** An adapter `base_url_env` of `ACCEPT_BASE_URL` silently sent "adapter" runs to the reference. **Fixed:** `adapter_problems` always refuses it, and `verify_run.py` reads the adapter's URL from `os.environ`.
- **H-2 (high).** Adapter values were used before their type was checked, which gave tracebacks. **Fixed:** one shape check, `rspec_lib.adapter_problems`, shared by `check_spec.py` and `verify_run.py`. Test: `test_a_malformed_adapter_is_one_error_line`.
- **H-3 (high).** The prompts didn't cover adapter faults, path refusals, an unreachable adapter, or UI tests staying on the reference. **Fixed:** in the judge, recorder, seeder and skill.
- **M-1 (bug).** A dead reference behind a live adapter was logged as failures. **Fixed:** both are checked. Test: `test_unreachable_adapter_or_reference_stops_as_not_run`.
- **M-2 (test gap).** Path templates, captures and query strings were untested. **Fixed:** the AC-001 test now uses a second app as the adapter, a `{param}` template and a `{capture}`, and asserts where the tasks were created. The refuse test now checks a query string.
- **In passing:** L-1 (the adapter starts for any kind of reference), L-3 (the shared inside-the-bundle rule) and F-3 (the seeder wording).

**Round 2: PASS** (`code-reviewer-r2.md`). Every round-1 finding is gone. Its new items were fixed before Ship, and `verify.py` passes:
- **N-1 (medium bug).** A seed refusal looped through fresh recorders. **Fixed:** a `blocked` reply, which the skill routes to the seeder or the user.
- **N-2 (medium, unconfirmed).** The judge could rule `spec-wrong` on a mistranslation. **Fixed:** with an adapter, `spec-wrong` needs evidence from the reference's own docs or `domain.md`.
- **N-3 (low).** The adapter now stops for any kind of reference.
- **L-3 leftover.** A symlinked seed that resolves outside the bundle is now refused, not skipped.

**Tickets**
- L-2: an `openapi.json` whose `servers` URL carries a base path would refuse every test. The CRM's contract isn't affected.
- L-4: no test covers the line that e2e and mobile tests stay on the reference's URL. The code branches on `runner == "http"`.

**Drift:** recorded in Deviations: `off_contract`, `adapter_problems`, the judge prompt, the test endpoint change, and the Public Surface key.

**Manual (AC-005):** the reviewer checked it against design points 5 and 6 in both rounds. The gaps it found are fixed above.
