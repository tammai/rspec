# Non-functional requirements

| ID | Quality characteristic (ISO/IEC 25010) | Requirement (measurable) | Features | Verification | Why | Tag |
|---|---|---|---|---|---|---|
| NFR-01 | Performance efficiency | | all | | | |

Verification: the test, monitor or review that proves the requirement (e.g. "k6 load test in CI", "alert on p95 > 300 ms", "WCAG 2.2 AA audit"). Required for every row when `goal` is `production`.

Cover at least: performance efficiency, reliability (realtime/sync, offline), security (auth, permissions), usability (accessibility), maintainability (observability), portability (i18n where relevant).
