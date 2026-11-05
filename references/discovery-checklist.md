# Discovery checklist

Use public, legitimate sources only. Prefer the most recent information: products change, and prior knowledge is a starting point, not the answer.

## Sources, in order of trust
1. **Official docs** (help center, docs site): the most precise description of behaviour.
2. **Changelog / release notes**: what exists now, what is new, what was renamed or removed. Read at least the last 12 months.
3. **Marketing feature pages and pricing page**: the module map and which features are plan-gated (enterprise-only features are usually Drop candidates).
4. **Public API reference** (REST/GraphQL schema, webhooks): the best source for entities, fields and relations.
5. **Open-source code** (if the product or its SDKs/apps are OSS): schema, migrations, client models. Check the licence first.
6. **Observed UI** (only if a browser tool is available and the user has an account): screens, states, empty states, keyboard shortcuts, error messages.
7. **Third-party reviews / tutorials**: only to fill gaps, mark as lower confidence.

## For each module, capture
- Screens and how they are reached (entry points, URLs/routes if visible).
- Primary user flows, step by step.
- Entities touched and their visible fields.
- States: empty, loading, error, permission-denied.
- Interaction details: keyboard shortcuts, drag and drop, inline edit, optimistic updates, realtime behaviour.
- Permissions: who can see / do what.
- Plan gating: which tier includes it.
- Recently added or changed features (with date).

## Confidence tags
Tag every factual line:
- `[docs]` stated in official docs, changelog or API reference
- `[observed]` seen in the running product
- `[inferred]` deduced, not confirmed. Say from what.
- `[3p]` from a third-party source

Every research file ends with a **Sources** list (title + URL + date accessed).

## Technical signals (for /rspec:tech)
- API style (REST, GraphQL, RPC), pagination, filtering, auth scheme.
- Realtime transport (WebSocket, SSE, polling) and what updates live.
- Offline / local-first behaviour, optimistic UI, conflict handling.
- File upload, search, notifications delivery (in-app, email, push).
- Public statements by the vendor about their architecture (engineering blog, talks).
