---
name: verify
description: >
  This skill should be used when the user runs /rspec:verify or asks to verify, prove or record a reverse
  spec's acceptance criteria against the running product (the reference): seed it, record each criterion as
  a test, run it, and report how much of the spec reached level 2. The pipeline runs it after audit, before
  handoff, when a reference is configured.
argument-hint: "[--scope mvp|full] [--only <feature or criterion IDs>]"
metadata:
  version: "0.13.0"
---

# /rspec:verify

Requires stage `tech` and a finished audit (`<spec>/audit/summary.md`). Runs only when `reference.run.kind` in `rspec.json` is `local` or `url`. Every figure in the report comes from `scripts/verify_report.py`, never from an agent's reply.

## 0. Decide (once)

When `progress.py` lists `decide`, ask once (AskUserQuestion; under autopilot take `autopilot.rules.verify` and `autopilot.reference`, ask nothing) whether to verify against a running reference, and how to reach it. Write the answer to `rspec.json` → `reference.run`:

- `kind`: `local` (a copy you run, e.g. an open-source product in Docker), `url` (a hosted product you may only read) or `none` (no verify: every criterion stays at level 1 or below, and the report says so).
- `base_url_env`: the environment variable holding the base URL, `ACCEPT_BASE_URL` unless the user names another `ACCEPT_*` one.
- `accounts`: account names only (`MEMBER`, `ADMIN`); each one's header line lives in `ACCEPT_ACCOUNT_<NAME>` (`Authorization: Bearer …` or `Cookie: sid=…`), set by the user, never written to a file.
- `writes`: `true` only for `local`. A `url` reference is read-only: criteria that need a write stay level 1 with reason `read-only reference`.
- `start` / `stop`: for `local`, the commands run from the project root.

For `url`, repeat the legal note (`${CLAUDE_PLUGIN_ROOT}/references/legal-notes.md`, Recording against a reference): recording respects the product's terms, reads only, and uses the user's own accounts. For `none`, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_report.py .`, which writes a summary with no level 2, and stop.

## 1. Preflight (main session)

1. `local`: run `reference.run.start` from the project root in the background.
2. Check that the variable named by `base_url_env` is set and the address answers an HTTP request; check that every `ACCEPT_ACCOUNT_<NAME>` for the listed accounts is set (never print their values).
3. Any failure: stop and name the failing item. Never record against a half-working reference. Under the pipeline, set `status` to `paused`.
4. The plan: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_report.py . --plan [--scope …] [--only …]` prints the criteria to record, grouped by feature. Verify scope is `--scope`, else `rspec.json` `verify_scope`, else `mvp`: Later criteria are recorded when a slice builds them (`--only <their IDs>`). `scope: full` still writes their stories and the report still counts them. Without `--only`, the plan skips criteria already at level 2 or with a recorded level 1 reason. Nothing to record → go to step 5.

## 2. Seed

Unless `writes` is false, run one `rspec:reference-seeder` with `<spec>`, `<contracts>`, the plan's feature IDs, `sources` and `reference.run` from `rspec.json`, and the plugin root. With `writes: false`, the seeder only notes the criteria that are `unseedable`.

## 3. Record

Launch one `rspec:criterion-recorder` per feature in the plan, **at most 4 in a single message** (more features: next message once those return). Give each, as paths and IDs and never pasted content: `<spec>`, `<contracts>`, its story file and the plan's criterion IDs for it, `<spec>/verify/seeds.md`, `reference.run` and the plugin root. A short agent per feature keeps context small (one recorder per module once reached 247 steps at about 250k tokens a step). A recorder that replies `not done` for steps gets a fresh recorder for what is left. Recorders run `scripts/verify_run.py`, which logs every run to `<spec>/verify/runs.jsonl`. **Exit 3, `reference unreachable`** (no answer, a gateway's 502-504, or a TLS certificate the client rejects): judge the criteria the recorder already reported `disputed`, stop every recorder you would launch next, run the preflight again and restart the reference. Its runs are logged `not run`, so nothing has to be cleaned up; re-run `--plan` and go on.

## 4. Disputes

For each criterion a recorder reports `disputed`, launch a fresh `rspec:verify-judge` (one per criterion, in one message) with: the criterion line and its story path, the test path, the reference's actual responses for its failing runs (the `detail` of its lines in `verify/runs.jsonl`, and the exact path of every `output` file its failing lines name: the folder is git-ignored, so the judge cannot search for them), `domain.md`, and the story's Differences. Never pass the recorder's reply. Then record the verdict with `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_report.py . --note <ID> <verdict> "<reason>"` and:

- `spec-wrong`: apply the corrected text through `/rspec:amend <ID>` (it logs the change and drops the criterion to level 0), then have one recorder re-record that criterion.
- `test-wrong`: one more recorder attempt for that criterion, with the judge's note. Once a test is in the bundle (`acceptance/manifest.json`), it changes only through `/rspec:amend <ID> --test`.
- `unrecordable`: nothing more; it stays level 1 with the reason.

## 5. Report

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_report.py .`: it decides level 2 (three passes in a row on one reference build, with the criterion's current text) and `flaky` (a pass and a fail on the same build and the same test content: runs of an earlier version of the test file do not count; kept out of level 2), and writes `<spec>/verify/summary.md`, `<spec>/verify/levels.json` and `<spec>/acceptance/manifest.json`. Then run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py .`, which writes level 2 into `criteria.lock.json`; fix errors. `local`: run `stop`, or end the background process. Delete `<spec>/verify/fail-output/` once the disputes are judged: it is git-ignored, but it can hold tokens. Add a line to `<changelog>`.

Reply with the summary's table rows and target line copied from `summary.md`, the flaky criteria, the disputes with their verdicts, and the unrecordable reasons. Target: MVP level 2 at least 90% for `local`; report only for `url`.

## Cost controls

- MVP only unless the verify scope is `full`; the plan skips what is already at level 2; `--only <feature or criterion IDs>` re-verifies a subset (re-record those, then report).
- One recorder per feature, briefed with paths; one saved browser state per account, reused by every UI test.
- A recorder stops a criterion after 2 attempts and a fresh judge takes it; the judge reads the full failing output, so no capture pass is needed.
- An unreachable reference stops the run at once (exit 3) instead of logging failures to re-run.
