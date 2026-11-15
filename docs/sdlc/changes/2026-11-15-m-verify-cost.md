# rspec 0.13.0: cheaper verify (full failing output, unreachable reference stops, flaky reset, MVP scope, plan by criterion)

## Why

**Request (verbatim):** please lead a cost optimization of the product-rebuild pipeline, including rspec changes and any companion plugins (sdlc, bug-hunter) where needed. (Relayed from the CRM rebuild session on the user's behalf; the CRM measured rspec:verify at about 540M tokens, 71% of the project, 14.3M fresh, about 48k fresh tokens per proven criterion.)

Where the CRM's verify cost went, and what each fix changes:
1. `verify_run.py` kept only the last 300 characters of a failing UI run. Judges never saw Expected and Received, so a capture pass and a second judge round were needed. → AC-001.
2. Docker died mid-sweep, and 181 tests logged connection-refused failures that then had to be run again. → AC-002.
3. One failed attempt, made while a test was being rewritten, pinned the criterion at flaky after three later passes. → AC-003.
4. Verify recorded all 1,446 criteria, Later ones included (about 160M tokens). Each slice's step 0 then re-verified them, re-recording whole features. → AC-004.
5. One long-lived recorder per module reached about 250k context per step. → recorder per feature and a fresh judge after two red attempts (skill and agent text).

**The user's words:** "Reset on test change": a run records a hash of the test file; old runs with no hash keep today's rule. "MVP by default": verify records MVP criteria; Later criteria are recorded per slice, and `full` is opt-in.

## Decisions

| Decision | Ruled out | Why |
|---|---|---|
| The full failing output goes to `<spec>/verify/fail-output/<criterion>-<UTC>.txt`, a folder `verify_run.py` git-ignores with its own `.gitignore` (`*`). `runs.jsonl` keeps the 300-character tail plus an `output` path | The full text in `runs.jsonl` | The output can hold tokens or cookies, and runs.jsonl is committed. The CRM deletes its copy after each use |
| Unreachable means the preflight TCP connect failed, or a run's failure says connection refused (`request failed: … refused`, `ECONNREFUSED`, `ERR_CONNECTION_REFUSED`). The run is logged `not run`, the loop stops, exit 3 | A retry | A recorder must stop the whole verify. A distinct exit code is what it can act on without judging the output |
| Flaky is judged on the runs of the current test content when any run carries `test_sha256` equal to the file's hash; otherwise on every run, as before | "Last 3 runs decide" | The user's choice. A test that really is flaky still mixes results within one version |
| Verify scope comes from `--scope`, then `rspec.json` `verify_scope`, then defaults to `mvp`. `scope` keeps deciding what stories are written and what the report counts | Verify following `scope` | The user's choice: a criterion recorded per slice later still counts in the report, because the report scope is unchanged |
| `verify_report.py --plan` prints which criteria to record, grouped by feature. It skips criteria already at level 2 or carrying a recorded level 1 reason, unless `--only` names them. `--only` takes feature or criterion IDs, of any priority but Drop | A new script | It reuses `status()`, the one place that decides level 2 |
| Windows: `verify_run.py` resolves `npx` and `maestro` through `shutil.which` before running | Leaving the CRM's wrapper in place | Without it, the e2e runner raises FileNotFoundError on Windows (npx is `npx.cmd`). It is also what lets AC-001's stub run there |

**Proposals not asked for:** None.

## Acceptance criteria

- **AC-001** Given a UI test whose runner fails with more than 300 characters of output, when `verify_run.py` runs it, then the runs.jsonl line names an `output` file under `verify/fail-output/` that holds the full output, and that folder is git-ignored.
- **AC-002** Given nothing answers at `ACCEPT_BASE_URL`, when `verify_run.py` runs a test, then it logs one `not run` line saying the reference is unreachable, makes no further runs, and exits 3.
- **AC-003** Given one failed run of an older version of a test, followed by three passes of its current version, when `verify_report.py` runs, then the criterion is level 2. When no run carries a test hash, the same failure still makes it flaky.
- **AC-004** Given a spec with `scope: full`, when `verify_report.py --plan` runs, then it lists MVP criteria only, without those already at level 2. `--scope full` adds Later features, and `--only <criterion ID>` lists just that criterion.

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | tests/test_verify.py › Verify.test_failing_ui_run_keeps_its_full_output | `python3 -m unittest discover -s tests -k test_failing_ui_run_keeps_its_full_output` |
| AC-002 | tests/test_verify.py › Verify.test_unreachable_reference_stops_as_not_run | `python3 -m unittest discover -s tests -k test_unreachable_reference_stops_as_not_run` |
| AC-003 | tests/test_verify.py › Verify.test_an_older_test_version_does_not_pin_flaky | `python3 -m unittest discover -s tests -k test_an_older_test_version_does_not_pin_flaky` |
| AC-004 | tests/test_verify.py › Verify.test_plan_lists_mvp_criteria_still_to_record | `python3 -m unittest discover -s tests -k test_plan_lists_mvp_criteria_still_to_record` |

## Must never break

- Level 2 still needs three passes in a row on one build, with the criterion's current text.
- A runs.jsonl written by 0.12.x (no `test_sha256`, no `output`) reports exactly as before, so product-rebuild's locked Gate 4 evidence does not move.
- runs.jsonl never holds more than the 300-character tail of a runner's output.

## Out of scope

- product-rebuild's side (bug-hunter tiers, boundary health guard, step 0 printing criterion IDs): product-rebuild 3.2.0.
- Playwright's Windows path-as-regex and working-folder quirks, which the CRM's wrapper also works around: left as a todo.

## Review

- **Recommended and chosen:** code, because `## Public Surface` adds `verify_report.py --plan` and `rspec.json` `verify_scope`; chosen by the trigger list (low risk, not asked).
- **Verdicts:** code-reviewer (built-in `code-review high --max-findings all`) → `.sdlc/.work/findings/2026-11-15-m-verify-cost/code-reviewer-r1.md` → FAIL — CR-1, 2, 4–10, 12; closing check → `code-reviewer-r2.md` → PASS (no high; medium bugs fixed in the same round, test first). The first r1 report was generated from a stale `cr-r1.json` left by an older feature; it was deleted and regenerated from this review's own findings file.
- **Fixed:**
  - Round 1, high:
    - **CR-1:** HTTP failure messages went into runs.jsonl whole. They now get the 300-character tail plus an output file.
    - **CR-4:** content no run carries could reach level 2. With a hashed history, only runs of the current content count.
    - **CR-5:** `--only` could plan criteria the holdout hid. Hidden criteria are never planned.
  - Round 1, medium:
    - **CR-2:** the probe allows 30 s, and a gateway's 502-504 means down.
    - **CR-6:** option values are no longer taken as the root.
    - **CR-7:** the plan uses the latest outcome.
    - **CR-8:** the recorder's reply after exit 3.
    - **CR-9:** manifest errors in `--plan` give an error line.
    - **CR-10:** an option with no value is rejected.
    - **CR-12:** the judge reads the exact output paths.
  - Round 2, medium:
    - **R2-1:** stdout names the output file, and the recorder reads it for any long failure.
    - **R2-2:** a rejected TLS certificate stops the run instead of failing every test.
    - **R2-3:** the hash reads CRLF as LF.
    - **R2-4:** `progress.py` counts per criterion.
    - **R2-5:** a recorder keeps its finished results after exit 3.
    - **R2-8:** the unreachable reason names scheme, host and port only.
    - **R2-10:** an empty `--only` and the `--scope=` form are refused.
    - **R2-11:** output file names carry microseconds.
  - Tests: `tests/test_verify.py`, 10 tests.
- **Decision (CR-3):** once hashed runs exist, unhashed runs from 0.12 stop counting even if their content was the same. This is the user's "reset on test change": an unhashed run's content is unknown, and the hashed series is the first evidence tied to content. Specs on 0.12 runs keep their levels until a criterion is run again.
- **Tickets:**
  - **R2-6:** `--note` values taken as the root, from before this change.
  - **R2-7:** outcomes carry no text hash, so a reason survives an amend.
  - **R2-9:** `amend.py` prints `--only <feature>`; it should print the criterion ID.
  - **R2-13:** the manifest parse is repeated.
  - **R2-14:** move to argparse.
  - **R2-16:** split the plan test per behaviour.
  - Playwright's Windows path quirks.
- **Drift and manual checks:**
  - **Deviations:**
    - `marketplace.json` version.
    - `verify_run.answers`, `save_output` and `test_hash`.
    - `verify_report.plan`, `hidden_criteria` and `opt`.
    - The `reference-seeder` example.
    - `progress.py`, edited before its test changed, so it was not seen red first.
  - No manual ACs.
- **Lessons filed:** `docs/sdlc/recurring-defects.md` (a cap applied to one runner's path only; a selection mode that skips a safety filter).
