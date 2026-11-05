# Production readiness

Nothing ships to production until every item is checked. Put the evidence after the item (a test, CI job, dashboard, runbook or document). An item that does not apply is checked and marked `(n/a: <reason>)`.

## Security
- [ ] Every threat in threat-model.md is mitigated and its test passes, or listed as an accepted risk
- [ ] Dependency and secret scanning run in CI
- [ ] Authentication: password policy or SSO, lockout or rate limiting on login
- [ ] Authorization tests for every role and tenant boundary
- [ ] Security headers, TLS everywhere, secure cookie settings

## Performance
- [ ] Load test proves every performance NFR at the expected peak
- [ ] Slow-query and payload-size budgets checked

## Reliability
- [ ] Service level objectives defined (availability, latency) with an error budget
- [ ] Automated backups, and a restore drill done and timed
- [ ] Graceful degradation and retries for every external dependency

## Observability
- [ ] Structured logs without personal data or secrets
- [ ] Metrics and alerts for each SLO, routed to someone on call
- [ ] Error tracking with release tagging

## Operations
- [ ] Deploy and rollback runbook, tried once
- [ ] Database migrations are reversible or have a tested forward fix
- [ ] Incident response: who is paged, where status is posted

## Privacy and compliance
- [ ] Personal data inventory: what is stored, why, how long
- [ ] Data export and deletion for a user
- [ ] Privacy policy and terms published
- [ ] Applicable regulations reviewed (GDPR, local data laws)

## Accessibility
- [ ] WCAG 2.2 AA audit of the main flows, issues fixed

## Legal
- [ ] Own product name and brand; no confusion with the original product
- [ ] Third-party and OSS licences reviewed, attributions in place
