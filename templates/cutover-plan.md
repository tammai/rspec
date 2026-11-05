# Cutover plan

Strategy: <rewrite | strangler | refactor>  
Old system: <what runs today>  
New system: <what replaces it>

## Before cutover
- Parity: every MVP feature's characterization tests pass against both old and new
- Data migration rehearsed on a production-size copy (see data-migration.md)
- Rollback rehearsed
- Users, support and integrators told the date and what changes

## Steps
<rewrite: freeze writes, final data migration, validation, switch traffic, smoke test, unfreeze>
<strangler: per slice, route the slice's paths to the new system behind a flag, watch, widen>
<refactor: per step, ship behind a flag, migrate in place, remove the old path>

## Go / no-go
- <checks and who decides>

## Rollback
- Trigger: <error rate, data mismatch, failed smoke test>
- Steps: <switch traffic back, restore data, unfreeze old system>
- Point of no return: <after which step rollback means forward fix>

## After cutover
- <watch period, decommission the old system and its data, keep backups until>
