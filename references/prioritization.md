# Prioritisation: MVP / Later / Drop

Decide against `goal` and `focus` in `docs/rspec.json`, not against the original product's importance.

## MVP
A feature is MVP if **any** of these hold:
- Without it the core loop does not work (e.g. for an issue tracker: create, view, update, list issues).
- It is the thing that gives the product its identity (e.g. keyboard-first command menu for Linear).
- It is explicitly in `focus` (the part the user wants to learn).
- It is a hard dependency of another MVP feature (auth before roles, teams before team-scoped IDs).

Keep the MVP small: aim for something one person can build in a few weeks. If the MVP list exceeds ~25 features, propose cuts.

## Later
Useful, fits the product, but the core loop works without it. Typical: advanced filters, templates, integrations, analytics, mobile, email/push notifications.

## Drop
- Enterprise or compliance features (SSO/SAML, SCIM, audit export, data residency) unless in `focus`.
- Features that only make sense at scale or with a sales team.
- Third-party-dependent features with no learning value for the user.
- Anything that would require copying protected content (brand assets, proprietary datasets).

## Goal adjustments
- `goal = personal-use`: favour features the user will actually use daily; drop collaboration features if they will use it alone.
- `goal = learn`: favour features that exercise the `focus` areas, even if they are not the most used ones.

Always write a one-line reason for every Drop and for any MVP that is not obviously core.
