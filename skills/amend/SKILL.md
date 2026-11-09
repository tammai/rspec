---
name: amend
description: >
  This skill should be used when the user runs /rspec:amend, or a builder, sdlc spec question or bug-hunter
  finding says an acceptance criterion is ambiguous, wrong or untestable after handoff, or a recorded acceptance
  test is wrong. It is the only path for a criterion or a recorded test to change once the spec is handed off.
argument-hint: "<criterion ID> \"<reason>\" | --finding <file> | <criterion ID> --test \"<reason>\""
metadata:
  version: "0.11.0"
---

# /rspec:amend

Changes one criterion (or adds one, or drops a wrong recorded test) and leaves the record: a changelog line, the criterion back at level 0 in `criteria.lock.json`, and a re-verify when a reference is configured. Never edit a criterion line or a file under `<spec>/acceptance/` by hand after handoff: builders and sdlc read the lock's hash, and a hand edit skips the record.

## Inputs

- `/rspec:amend <criterion ID> "<reason>"`: the criterion is wrong or unclear.
- `/rspec:amend --finding <file>`: a `finding-v1` file (contracts C6): an sdlc spec question (`.sdlc/.work/spec-questions/<feature>.json`, class `spec-gap`) or a bug-hunter spec gap. Accepted when `contracts.py` routes it to `rspec`: a reproduced `spec-gap`, or a spec question (`source: sdlc-question`, `verified_by.result: "not run: spec question"`; its `question` is what to settle). Any other unreproduced finding is refused. Its ID goes into the changelog line.
- `/rspec:amend <criterion ID> --test "<reason>"`: the recorded test is wrong, the criterion is right (a judge's `test-wrong`, or a builder's question about a bundle test).
- A missing criterion: `/rspec:amend <feature ID> --new "<reason>"`.

## Steps

1. Read the criterion line, its story (Failure modes, Differences, Sources), `<spec>/domain.md` and, for a finding, its `observed` and `repro` (a spec question has neither: read its `question`).
2. Decide the new text. The reference is the oracle: prefer what it was observed to do (`[observed]`) or what a source states; a choice the rebuild makes on purpose is a departure (an `Open: departure:` line, decided as in `/rspec:stories`), not an amend. Ask the user (AskUserQuestion) when the reason or finding does not settle the text, and always when the change touches the `then` of an MVP criterion. Under autopilot, apply what the evidence settles and park the rest under `## Parked` in `<spec>/autopilot-log.md`.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/amend.py . <ID> --text "<Given …, when …, then …. \`[tag]\`>" --reason "<reason>"` (add `--finding <file>`, or use `--new` with the feature ID, or `--test` with no `--text`). It refuses text that breaks contracts C1 and writes nothing then; fix the text and run it again. It writes the changelog line, drops the criterion to level 0 and runs `check_spec.py`, which regenerates the lock.
4. When it prints `next: /rspec:verify --only <feature>`, run `/rspec:verify --only <feature>` so the criterion is recorded again against the reference.
   When the check then warns `tech is stale` (the contracts were written before this change): if the new text changes an operation, field, status code or rule in `<contracts>`, update them (or run `/rspec:tech` for the feature); either way, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py . --mark-tech` once the contracts agree.
5. Reply with the criterion's old and new text, the changelog line, and its level after the re-verify. For an sdlc spec question, say that the blocked part unblocks once sdlc sees the new hash in `criteria.lock.json`.
