# Lock file stays LF and gates can check without writing it

## Why

Request: "product-rebuild S1-S4 items 4h and 5a: (1) /rspec:init writes a .gitattributes line `<spec>/criteria.lock.json text eol=lf` so git checkout on Windows doesn't write CRLF; (2) check_spec.py gets a read-only flag (--no-lock) that skips writing criteria.lock.json, for gates that hash it; (3) agents/criterion-recorder.md: UI tests wait for hydration before filling forms."

The CRM rebuild (product-rebuild issue list S1–S4, items 4h and 5a) had two problems. Its gate-4 hash over `criteria.lock.json` broke when `check_spec.py` rewrote the lock, and again when `git checkout` restored the lock with CRLF (`core.autocrlf=true`). `check_spec.py` already writes the lock with LF (since 0.11), so the CRLF comes from git, not from us. Separately, recorded Playwright tests filled a Nuxt form before hydration, so the values were lost when tests ran in parallel.

## Acceptance criteria

- **AC-001** `init_spec.py` adds `<spec>/criteria.lock.json text eol=lf` to the project root's `.gitattributes`, creating the file if missing, keeping existing lines, and not duplicating the line on a rerun (a rerun is how an existing spec gets it).
- **AC-002** `check_spec.py --no-lock` runs every check and still exits 0 or 1 as before, but leaves `criteria.lock.json` byte-for-byte as it was, even when the stories changed.
- **AC-003** `agents/criterion-recorder.md` tells the recorder that a UI test waits for the page to hydrate before filling a form, and checks the filled value.

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | `tests/test_init.py` › `test_gitattributes_keeps_lock_lf` | `python3 -m unittest discover tests -k test_gitattributes_keeps_lock_lf` |
| AC-002 | `tests/test_criteria_ids.py` › `test_no_lock_leaves_lock_untouched` | `python3 -m unittest discover tests -k test_no_lock_leaves_lock_untouched` |
| AC-003 | manual | Prompt wording; no script behaviour to test. Checked by reading the recorder's UI rule. |

## Must never break

- `check_spec.py` without `--no-lock` writes the lock exactly as before (existing lock tests).
- `--mark-tech` and the stale-tech warnings work with or without `--no-lock`.
- `init_spec.py` reruns keep every file the user already has.

## Decisions

| Decision | Chosen | Ruled out |
|---|---|---|
| Fix CRLF where | `.gitattributes` from init | Normalising line endings in product-rebuild's hash: that's product-rebuild's call, told in the reply |
| Read-only check | opt-in `--no-lock` flag | Making check read-only by default: the lock is meant to be written by `/rspec:check` (contracts C3) |

## Out of scope

- The builder's own E2E tests (the CRM sign-up form, `--workers=1`): product-rebuild's builder side.
- product-rebuild's gate-4 hash: they adopt `--no-lock` or normalise there.

## Review

- **Fired:** code review (Public Surface adds `check_spec.py --no-lock`); low risk, run without asking. Built-in `code-review high --max-findings all`, 2 rounds.
- **Round 1, FAIL → fixed.** Highs: CR-2, the CHANGELOG told users to rerun `init_spec.py` on an existing spec, which can scaffold a second spec, so `check_spec.py` now adds the line from the real layout (`pin_lock_lf` in `scripts/rspec_lib.py`); CR-3, `--no-lock` passed a stale lock, now an error; CR-4, `--no-lock --mark-tech` wrote `rspec.json`, now refused. Bugs also fixed: CR-1, a CRLF lock is rewritten LF; CR-5, init reports an appended `.gitattributes` as `updated`; CR-10, the hydration wording no longer suggests a flag that can hang; CR-11, the created branch is tested. Also fixed: CR-6 docstring, CR-8 `write` parameter, CR-9 `/rspec:check` documents `--no-lock`.
- **Round 2, PASS** (no highs). Bugs fixed with tests: `--no-lock` compares bytes, so a CRLF lock fails it; an unwritable `.gitattributes` is a WARN, not a traceback; tests for the `--mark-tech` refusal and init's `updated` key; clearer error wording.
- **Tickets:** `acceptance/manifest.json` and recorded test files aren't pinned LF, though Gate 4 hashes them too (told to product-rebuild); a spec folder at the repo root pins `.gitattributes` outside the repo; spec paths with spaces or glob characters; equivalent rule spellings aren't recognised; init's pin is redundant on reruns; `--no-lock` doesn't warn when the pin is missing.
- **Drift:** `scripts/rspec_lib.py` (shared pin helper), the `write_lock` `write` parameter, and test changes after review, each in Deviations with a fresh red at Base.
- **Manual:** AC-003, checked by reading `agents/criterion-recorder.md`'s UI rule. It says to wait for hydration before the first fill and to assert each value held.
