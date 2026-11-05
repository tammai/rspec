# Threat model

Method: STRIDE per entry point. Entry points come from `openapi.json`, `asyncapi.json` and the screens that accept input. Each threat has a mitigation that is an NFR or a feature ID, so it gets built and tested.

## Assets and trust boundaries
- <asset>: <why it matters>
- <boundary>: <what crosses it>

## Threats
| ID | STRIDE | Entry point | Threat | Mitigation | Tag |
|---|---|---|---|---|---|
| T-01 | <Spoofing / Tampering / Repudiation / Information disclosure / Denial of service / Elevation of privilege> | <operationId or screen> | <what an attacker does> | <NFR-NN or F-CODE-NN> | <tag> |

## Accepted risks
- <risk>: <why accepted, by whom>
