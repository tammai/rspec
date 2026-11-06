# Domain rules

The one place for rules that many stories, NFRs and contracts share. Stories, NFRs, ADRs and contracts cite these sections (`domain.md §Roles`) instead of restating the rule; a change is made here first. `/rspec:check` compares the contracts with the two tables below.

## Roles and permissions
Roles, lowest to highest: <guest, member, admin>. One row per action that not every role may take. `Operations` lists the `operationId`s that perform it; each of those carries `x-roles` with exactly the roles marked yes.

| Action | Operations | <guest> | <member> | <admin> |
|---|---|---|---|---|
| <Create an API key> | <createApiKey> | no | no | yes |

## Enumerations
One row per value set used in more than one place. `Name` is the property name the schemas use; every schema property of that name with an `enum` has exactly these values.

| Name | Values | Notes |
|---|---|---|
| <role> | <guest, member, admin> | |

## Limits and defaults
| Rule | Value | Source |
|---|---|---|
| <Team key length> | <2–5 uppercase letters or digits> | <[docs] URL> |

## Identifiers
- <Issue: team key + per-team number, e.g. ENG-12>
