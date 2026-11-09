# Rules-recall fixture

A recall test for OSS-mode discovery: how many of a codebase's known business rules does a spec record?
Ported from product-rebuild 3.0.0 (`docs/MIGRATION-3.md` row 9), where it scored lane R's Rule Cards.

- `reference-src/`: about 250 lines of Rails billing code, written for this fixture.
- `gold.yaml`: the answer, 33 rules, each with its locations (path, line range), test values and, for the
  classes hardest to extract (defaults, error handlers, rules split across files), a `hard` reason.

## Run it

1. Copy `reference-src/` **outside this repo**, `git init` and commit it, so there is a real commit to cite.
2. In a fresh project, run `/rspec:init` (open source, code: true, pointing at that copy), then `/rspec:discover`,
   `/rspec:features` and `/rspec:stories`. **Never let an agent see `gold.yaml`**: one that has read the answer
   is copying it.
3. Score: `python3 <rspec>/scripts/rules_recall.py <project> --model <tier>`.

A gold rule is **found** when a `domain.md` line, or a criterion tagged `[code]`, cites `path:line` inside one of
the rule's locations. Only an exact token counts (`app/models/invoice.rb:16` or `…:16-18`, no spaces, start before
end); a GitHub `#L` link, a backslash path or a comma list is not read. **Strict** also needs every `values` group
in that line's text: numbers as whole tokens compared by value (`25.00` is 25, `19%` is not 9%), words as
substrings. The score decides nothing;
a change to the module explorer or story writer briefs states its before-and-after numbers in `CHANGELOG.md`.

The gold set is complete only as far as anyone has checked. A citation the report lists as matching no gold
rule, whose claim is true of the cited line, means the gold set is short: add the rule and re-score.
**Changing `reference-src/` means changing `gold.yaml`'s line numbers in the same commit.**
