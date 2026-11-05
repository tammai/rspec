<!-- rspec:handoff -->
## Building <working name> from the spec (with sdlc)

The reverse-engineered SRS in `docs/` is the written spec for this rebuild. sdlc runs the build; rspec's pipeline starts one sdlc feature per slice of `docs/build-plan.md`.

- One sdlc feature per build-plan slice, one backlog part per rspec feature (`F-…`) in that slice, in build-plan order.
- The change file points to the spec instead of restating it. Each acceptance criterion cites the story it proves, as `docs/features/<file>.md §<feature ID>`, e.g. `**AC-001** docs/features/F-ISS-01-create-issue.md §F-ISS-01: Given …, when …, then …`. `verify.py trace` checks these.
- API work follows `docs/openapi.json` (and `docs/asyncapi.json`); data types follow `docs/schemas/`. Change the contract first, then the code.
- ADRs in `docs/decisions/` marked Accepted are binding decisions; record a change as a new ADR that supersedes one.
- sdlc tracks progress. Do not edit `status` in the story files; `/rspec:pipeline` sets it when a slice's sdlc feature is done.
- Do not use the original product's name, logo, text or images.
- After changing anything in `docs/` outside `docs/sdlc/`, run `python3 <plugin root>/scripts/check_spec.py .`.
<!-- /rspec:handoff -->
