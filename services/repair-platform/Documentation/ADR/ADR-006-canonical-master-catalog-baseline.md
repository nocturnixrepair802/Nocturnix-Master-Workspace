# ADR-006: Canonical Master Catalog Baseline

- Status: Accepted
- Date: 2026-07-22

## Context

The repository already contains a canonical master catalog architecture draft in `Documentation/MASTER_CATALOG_ARCHITECTURE.md`.
A separate legacy raw import artifact, `D:/Business Portal/300_Pricing/Legacy/Raw Import Data.xlsx`, has been identified for analysis.
This raw workbook contains schema noise, duplicate rows, missing supplier/manufacturer references, mixed-type SKU values, and zero pricing/cost values.

The platform needs a formal decision that the architecture document is the authoritative baseline for canonical master catalog design and legacy import migration planning.

## Decision

- Accept `Documentation/MASTER_CATALOG_ARCHITECTURE.md` as the canonical architecture baseline for the master catalog and migration planning.
- Treat legacy raw import artifacts as read-only staging inputs, not authoritative sources.
- Use the canonical architecture document as the reference for table definitions, data ownership, import workflow, validation strategy, and update workflow.
- Base legacy import migration on companion analysis and planning documents.
- Create and maintain the following supporting documentation as part of the migration effort:
  - `Documentation/RAW_IMPORT_ANALYSIS.md`
  - `Documentation/LEGACY_IMPORT_MIGRATION_PLAN.md`
  - `Documentation/LEGACY_TO_CANONICAL_FIELD_MAP.md`

## Consequences

- The master catalog architecture is anchored to a single documented baseline.
- Legacy imported workbooks are handled through explicit staging, normalization, and validation.
- No workbook or source code changes are performed as part of this decision.
- Migration planning must explicitly account for raw import data quality issues and schema noise.

## Alternatives considered

- Treat `Raw Import Data.xlsx` as canonical and load it directly: rejected because the workbook has noisy headers, duplicate records, missing reference values, and inconsistent typing.
- Continue without a formal ADR: rejected because migration planning requires an explicit, agreed baseline and governance record.
- Use only workbook validation code without a canonical architecture document: rejected because it does not provide a stable, business-facing architecture baseline.

## References

- `Documentation/MASTER_CATALOG_ARCHITECTURE.md`
- `Documentation/RAW_IMPORT_ANALYSIS.md`
- `Documentation/LEGACY_IMPORT_MIGRATION_PLAN.md`
- `Documentation/LEGACY_TO_CANONICAL_FIELD_MAP.md`
