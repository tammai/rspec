# Writing rules for all rspec documents

- Write in the language set in `<spec>/rspec.json` (`lang`). Keep IDs, file names, template section headings (e.g. `## Acceptance criteria`) and template keywords (MVP, Later, Drop) in English; `/rspec:check` looks for those headings.
- Keep story frontmatter keys, the Given / When / Then keywords and JSON contract keys in English too.
- Own words only for the rspec track; see legal-notes.md. In the modernize track describe behaviour in plain words, but quoting your own code, messages and docs is fine.
- One fact per line, tagged with a confidence tag from discovery-checklist.md.
- Prefer concrete, testable statements ("Issue IDs increment per team: ENG-1, ENG-2") over vague ones ("issues have nice IDs").
- Feature IDs: `F-<MODULE CODE>-<NN>`, two-digit sequence, never reused. Module codes are 2–4 uppercase letters, defined in `<spec>/rspec.json`.
- Traceability: every API operation, schema and event lists the feature IDs it serves in `x-features`; every NFR names the features it constrains or `all`.
- When the rebuild deliberately differs from the original, say so explicitly and link the ADR.
- **Acceptance criteria quality bar** (every story, whatever the build engine):
  - Concrete: use example data a test can use as is: an identifier (`ENG-12`), a value (priority Urgent), a count (three selected issues), a name typed ("prio").
  - Evidenced: end each criterion with its confidence tag (`[docs]`, `[api]`, `[observed]`, `[3p]`, `[code]` or `[inferred]`). The tag is for the expected result (the "then"), not the topic: `[docs]` or `[api]` only when the source states that result. If the source covers only part of it, split the criterion or tag it `[inferred]`. A rebuild choice is `[inferred]` and says so in Differences.
  - One behaviour per criterion, observable by a user or an API client, and within the feature's row in features.md.
- Do not invent precision. If a limit or behaviour is unknown, write `unknown` and add it to the module's open questions.
