# Writing rules for all rspec documents

- Write in the language set in `<spec>/rspec.json` (`lang`). Keep IDs, file names, template section headings (e.g. `## Acceptance criteria`) and template keywords (MVP, Later, Drop) in English; `/rspec:check` looks for those headings.
- Keep story frontmatter keys, the Given / When / Then keywords and JSON contract keys in English too.
- Own words only; see legal-notes.md.
- One fact per line, tagged with a confidence tag from discovery-checklist.md.
- Prefer concrete, testable statements ("Issue IDs increment per team: ENG-1, ENG-2") over vague ones ("issues have nice IDs").
- Feature IDs: `F-<MODULE CODE>-<NN>`, two-digit sequence, never reused. Module codes are 2–4 uppercase letters, defined in `<spec>/rspec.json`.
- Traceability: every API operation, schema and event lists the feature IDs it serves in `x-features`; every NFR names the features it constrains or `all`.
- When the rebuild deliberately differs from the original, say so explicitly and link the ADR.
- Do not invent precision. If a limit or behaviour is unknown, write `unknown` and add it to the module's open questions.
