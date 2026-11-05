# Data migration

From: <current stores, e.g. MySQL 5.7 `app` schema, S3 bucket `uploads`>  
To: <target stores>  
Strategy: <rewrite: one final migration at cutover | strangler: per slice, with sync back | refactor: in-place migrations>

## Mapping
| ID | Old (store.table) | New (entity) | Transform | Validation |
|---|---|---|---|---|
| M-01 | <store.table> | <entity schema> | <field mapping, type and code conversions, defaults> | <row counts, checksums, sampled diff> |

## Volumes and timing
- <table>: <rows, size, growth>; estimated migration time: <measured on a copy>

## Not migrated
- <table or data>: <why: unused, derived, retired with F-XXX-NN>

## Rehearsal
- Run on a production-size copy: <date, duration, issues found>

## Rollback
- <how to return to the old data if the cutover is aborted, and the point of no return>
