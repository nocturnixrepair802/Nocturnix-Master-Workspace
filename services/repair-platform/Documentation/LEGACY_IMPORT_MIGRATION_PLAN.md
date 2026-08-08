# Legacy Import Migration Plan

## Objective

Define a read-only migration plan for legacy import artifacts into the canonical master catalog baseline documented in `Documentation/MASTER_CATALOG_ARCHITECTURE.md`.
This plan focuses on the legacy file `D:/Business Portal/300_Pricing/Legacy/Raw Import Data.xlsx` and preserves the artifact as a staging input.

## Principles

- Preserve legacy workbooks as read-only sources of truth for analysis.
- Normalize legacy values to canonical lookup IDs and enumerations before load.
- Validate referential integrity and duplicate removal as separate stages.
- Record import provenance and version metadata for every migration batch.
- Use the canonical architecture document as the reference for target tables, keys, and ownership.

## Migration phases

### Phase 1: Artifact capture and preservation

1. Archive a copy of the raw workbook in a read-only staging area.
2. Record the source path, file timestamp, and extraction method.
3. Document the raw worksheet name and row/column counts.
4. Confirm that no workbook modifications are made during analysis.

### Phase 2: Raw schema normalization

1. Remove workbook-specific header noise:
   - Ignore `⬅ Return to Table of Contents`.
   - Ignore blank header columns.
   - Ignore `Column1`.
2. Use the remaining headers as the staging payload.
3. Normalize field names to canonical staging names.
4. Convert `SKU` values to a consistent string format.
5. Normalize numeric fields for `Price` and `Cost` using explicit conversion rules.
6. Preserve `Updated At` and `Created At` as source audit metadata fields.

### Phase 3: Data quality remediation

1. Identify and collapse duplicate rows based on canonical staging key combinations.
2. Identify duplicate `SKU` values and group them for business review.
3. Flag rows with missing `Manufacturer` or `Supplier` values.
4. Flag rows with `Price == 0` or `Cost == 0` for explicit business validation.
5. Flag numeric type anomalies such as string-encoded costs.
6. Flag rows with missing optional but meaningful fields like `Serial Number`, `Bin`, and `Note`.

### Phase 4: Canonical mapping and validation

1. Map normalized staging fields to canonical target fields using `Documentation/LEGACY_TO_CANONICAL_FIELD_MAP.md`.
2. Validate lookup references for manufacturers, suppliers, categories, types, and conditions against canonical lookup tables.
3. Resolve or reconcile missing lookups through data enrichment or business rules.
4. Validate enumeration memberships for `Condition`, `Tax Free`, and other controlled values.
5. Validate legacy monetary semantics using `Legacy Retail Price` and `Legacy Cost`; keep formulas, margins, and policies in `pricing_rules` rather than mapping these raw values directly to pricing rule tables.

### Phase 5: Staging load and verification

1. Load cleansed records into a staging table or temporary import workspace.
2. Run the full suite of canonical validation checks:
   - table presence and required columns
   - primary key uniqueness
   - referential integrity
   - enumeration constraints
   - monetary value normalization
3. Track staging identity fields for each record:
   - `Import Batch ID`
   - `Source Workbook`
   - `Source Worksheet`
   - `Source Row Number`
   - `Legacy SKU`
   - `Canonical ID`
   - `Duplicate Group ID`
   - `Record Category`
   - `Destination Dataset`
   - `Transformation Status`
   - `Review Status`
   - `Validation Notes`
4. Generate a migration report capturing row counts, rejected rows, transformed fields, and provenance.
5. Obtain stakeholder signoff before promoting staging records into the canonical master catalog.

### Phase 6: Controlled ingestion

1. Insert validated records into the canonical master catalog tables or planned canonical staging tables.
2. Record the migration batch metadata, including:
   - source workbook identifier
   - import date
   - transformation version
   - data owner and reviewer
3. Archive the prior canonical artifact version before making the new canonical dataset active.

## Acceptance criteria

- Legacy raw import data is preserved in the archive.
- No raw workbook cells are edited in place.
- Clear canonical field mapping is documented and used.
- Duplicate SKUs and duplicate rows are resolved or explicitly approved for ingestion.
- Missing manufacturer/supplier references are reconciled or documented as unresolved.
- `Price` and `Cost` values are normalized to numeric canonical types.
- Source audit metadata from `Updated At` and `Created At` is preserved.
- The canonical architecture baseline remains the reference point for target tables and relationships.
