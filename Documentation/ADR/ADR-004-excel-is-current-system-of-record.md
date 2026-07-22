# ADR-004: Excel Is the Current System of Record

- Status: Accepted
- Date: 2026-07-22

## Context

The application loads configured tables from
`Data/Nocturnix_Master_Database.xlsm`. The workbook contains current operational and
reference data, while durable application write and transaction support remain
incomplete. A storage migration during engine contract repair would compound risk.

## Decision

- Excel remains the current system of record during stabilization and engine
  migration.
- Workbook files and columns are not changed without a separately reviewed,
  backed-up migration.
- Temporary repository adapters may translate legacy column names without modifying
  workbook storage.
- Planned persistence boundaries should allow Excel to be replaced later without
  rewriting GUI or business rules.

## Consequences

- Existing data remains usable while contracts are documented and tested.
- Schema limitations must be handled explicitly rather than hidden.
- Safe write, backup, validation, and rollback mechanisms remain prerequisites for
  production persistence.
- Migration documentation must distinguish current tables from planned tables.

## Alternatives considered

- Migrate immediately to SQLite or another database: rejected because it combines
  storage migration with active architecture repair.
- Treat in-memory DataFrames as the system of record: rejected because they are not
  durable.
- Modify the workbook opportunistically during refactoring: rejected because it lacks
  controlled backup and migration validation.
