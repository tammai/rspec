# Evidence trust: no level 1 for inferred criteria, scoped negative claims, research question checklist

## Why

**Request (verbatim):** Tighten evidence trust, ideas learned from morluto/rea: (3) [inferred] criteria must never reach level 1 via audit sampling, and NOT-CONTRADICTED alone must not promote a criterion — audit_sample.py --levels plus contracts/v1 C3 wording plus tests; (2) a claim that something doesn't exist must state its search scope, or it is tagged [inferred] — rule in references/writing-rules.md plus the module-explorer and coverage-auditor prompts; (5) module-explorer research gets a question checklist and its reply reports answered/partly/open counts.

A criterion's level tells a builder how far to trust it. Today `audit_sample.py --levels` (line 17, `CONFIRMED = {"SUPPORTED", "NOT-CONTRADICTED"}`, and the population rule at line 75) raises `[inferred]` criteria to level 1: a guess the fact-checker found nothing against counts the same as a fact a source states, and a clean `[inferred]` sample promotes the whole unsampled `[inferred]` population too. The lock then overstates the spec. The other two items close the same gap upstream: "I didn't find it" written as "it doesn't exist", and research that ends without saying which questions it left open.

## Decisions

| Decision | Ruled out | Why |
|---|---|---|
| `[inferred]` criteria stay level 0 after the audit, sampled or not; level 1 needs `SUPPORTED` | Keeping `NOT-CONTRADICTED` as a weaker level 1 | NOT-CONTRADICTED is the fact-checker's verdict only for `[inferred]` (`agents/fact-checker.md:33`); not contradicted is not evidence. Retagging the criterion with a source is how it earns level 1 |
| `[inferred]` stays in the fact-check sample | Dropping it from the draw | The sample still catches CONTRADICTED and DECISION on guesses, which are Important findings |
| C3 wording in `contracts/v1/CONTRACTS.md` is not edited here | Editing the vendored copy | Constitution I: `contracts/v1/` is vendored byte-identical and verified by `test_contracts_vendor.py`. The stricter rule still satisfies C3's level 1 (every criterion it raises was sampled and confirmed, or is in a clean audited population); the wording change goes to the contracts' source |
| The negative-claim and question-checklist rules are prompt and template wording, not a script check | A `check_spec.py` check | Constitution II puts mechanical rules in scripts; telling a scoped absence claim from an unscoped one in prose is judgement, not a token match |

**Proposals not asked for:** None.

## Acceptance criteria

- **AC-001** Given an audit whose `[inferred]` sample is all NOT-CONTRADICTED, when `audit_sample.py --levels` runs, then no `[inferred]` criterion (sampled or unsampled) is in `levels.json` and each stays level 0 in the lock, while `[docs]` criteria confirmed SUPPORTED in the same run reach level 1.
- **AC-002** Given a non-inferred criterion whose verdict is NOT-CONTRADICTED (a fact-checker slip), when `--levels` runs, then it stays level 0.
- **AC-003** `references/writing-rules.md` and `references/discovery-checklist.md` state that a claim that something does not exist (no such feature, setting, limit or screen) names where it was searched, else it is `[inferred]`; a bounded search never proves absence. `agents/module-explorer.md` and `agents/coverage-auditor.md` apply it (the explorer to its research, the auditor to Drop rows and capabilities it marks absent).
- **AC-004** `templates/research-module.md` has a `## Questions` checklist (each question, the evidence that would answer it, and `answered`, `partly` or `open`), `agents/module-explorer.md` tells the explorer to write the questions before researching and mark each at the end, and its reply reports the answered / partly / open counts.
- **AC-005** The docs that restate the level 1 rule (`skills/audit/SKILL.md` step 4, `agents/fact-checker.md`, the script's docstring) say `[inferred]` never reaches level 1 by audit, and `CHANGELOG.md` `[Unreleased]` records the change and that existing specs pick it up by rerunning `audit_sample.py --levels`.

## Acceptance tests

| AC | Test | Run |
|---|---|---|
| AC-001 | tests/test_audit.py › test_inferred_criteria_never_reach_level_1 | `python3 -m unittest discover tests -k test_inferred_criteria_never_reach_level_1` |
| AC-002 | tests/test_audit.py › test_not_contradicted_on_a_sourced_tag_stays_level_0 | `python3 -m unittest discover tests -k test_not_contradicted_on_a_sourced_tag_stays_level_0` |
| AC-003 | manual | Prompt and reference wording; its effect shows only in an agent run. Checked by reading the four files against the AC |
| AC-004 | manual | Template and prompt wording; checked by reading the template and the explorer prompt against the AC |
| AC-005 | manual | Documentation; checked by grepping for the old rule's wording (`NOT-CONTRADICTED`, `no CONTRADICTED`) |

## Must never break

- Sourced criteria (`[docs]`, `[api]`, `[observed]`, `[code]`) reach level 1 exactly as before: SUPPORTED when sampled, or unsampled in a population with no CONTRADICTED; an edited criterion or one with its own finding never does (`test_audit_verdicts_raise_criteria_to_level_1`).
- `contracts/v1/` stays byte-identical to its manifest.

## Out of scope

- The C3 wording in the contracts' source (see Decisions); a follow-up for whoever owns `contracts/v1`.
- A rules-recall run (`scripts/rules_recall.py`): no baseline is recorded yet, and the explorer change adds no rule-finding instruction.
- Tracked unknowns (`unknowns.yaml`), HAR-derived API facts and route inventory from the same comparison: separate features if wanted.
- A version bump; this lands under `[Unreleased]`.

## Review

No review ran: low risk, no trigger fired; AC-001 and AC-002 red then green (verify.py). Manual ACs checked by me against the files: AC-003 the absence rule is in references/writing-rules.md and discovery-checklist.md, applied in agents/module-explorer.md step 6 and agents/coverage-auditor.md step 2 (Drop rows); AC-004 templates/research-module.md has ## Questions, module-explorer steps 0 and 7 and its reply carry the counts; AC-005 grep finds no remaining text that counts NOT-CONTRADICTED as confirmed (skills/audit step 4, fact-checker severity, script docstring updated), CHANGELOG [Unreleased] has the entries. Deviation: verify ran with a python->python3 shim on PATH because the config's test command calls python. Out of scope follow-up: C3 wording in the contracts' source.
