# Raw Import Workbook Analysis

## Scope

This document captures a read-only analysis of the legacy workbook artifact `D:/Business Portal/300_Pricing/Legacy/Raw Import Data.xlsx`.
The workbook is a staging-level source and is not considered authoritative for the canonical master catalog.
All observations are based on the workbook contents and the current canonical architecture baseline in `Documentation/MASTER_CATALOG_ARCHITECTURE.md`.

## Workbook metadata

- File: `Raw Import Data.xlsx`
- Worksheet: `37. Raw Import`
- Total data rows: 743
- Total columns: 21

## Header and schema observations

- The header row includes a navigation placeholder column: `⬅ Return to Table of Contents`.
- Two adjacent blank header columns appear before the canonical payload fields.
- The workbook contains an entirely empty placeholder column named `Column1`.
- The effective payload begins at `SKU` and includes `Group`, `Category`, `Type`, `Manufacturer`, `Name`, `Price`, `Cost`, `Stock`, `Serial Number`, `Condition`, `Tax Free`, `Bin`, `Supplier`, `Note`, `Updated At`, and `Created At`.
- These workbook header anomalies indicate this file is a downstream export or staging artifact rather than a normalized canonical table.

## Data quality observations

- `SKU` is populated in every row, but it has mixed value types: 93 integer values and 650 string values.
- `Manufacturer` is missing in 93 rows.
- `Supplier` is missing in 650 rows.
- `Serial Number` is missing in 706 rows.
- `Bin` is missing in 716 rows.
- `Note` is missing in 718 rows.
- `Column1` is blank for all 743 rows and should be ignored.

### Pricing and cost quality

- `Price` is present for all rows.
- `Cost` is present for all rows.
- 232 rows have `Price` equal to 0.
- 604 rows have `Cost` equal to 0.
- `Cost` contains 4 rows encoded as text rather than numeric values.
- No negative values were observed for `Price` or `Cost`.

### Duplicates and uniqueness

- There are 315 duplicate full-row occurrences.
- There are 323 duplicate `SKU` occurrences across the 743 rows.
- This suggests a high duplication rate in the raw import artifact and confirms that de-duplication is required before canonical ingestion.

## Value distributions

### Top `Group` values

- `Miscellaneous Repair`: 416 rows
- `Samsung Screen Repair`: 104 rows
- `iPhone Screen Repair`: 54 rows
- `Screen Adhesive`: 50 rows
- `Miscellaneous Tool`: 20 rows

### Top `Category` values

- `Repair`: 574 rows
- `Part`: 84 rows
- `Device`: 46 rows
- `Tool`: 38 rows
- `Accessory`: 1 row

### Top `Type` values

- `Repair - Phone`: 574 rows
- `Part - Phone`: 62 rows
- `Device - Phone`: 41 rows
- `Tools`: 38 rows
- `Part - Other`: 16 rows

### `Condition` distribution

- `New`: 699 rows
- `Damaged`: 24 rows
- `Used`: 20 rows

### Top `Supplier` values

- `Injured Gadgets`: 75 rows
- `MobileSentrix`: 18 rows

## Interpretation

- The workbook appears to represent a mixed inventory/pricing staging dataset rather than a structured canonical catalog.
- Many records are low-value staging rows such as repair items, parts, and tools.
- The dominant category is `Repair`, and the dominant type is `Repair - Phone`, suggesting the file is largely repair-service and repair-part pricing data.
- The high incidence of missing `Supplier` data and zero `Cost` values suggests the import was produced before supplier and cost normalization.
- The raw file contains navigation and placeholder artifacts that should be removed during transformation.
- `Legacy SKU` is not automatically a canonical primary key because duplicate SKU occurrences exist and SKU values mix numeric and string types.

## Destination candidate counts

- `master_services`: 574 rows
- `parts_catalog`: 82 rows
- `master_devices`: 8 rows
- `tool_catalog`: 38 rows
- `accessories_catalog`: 1 row
- `inventory_items`: 40 rows
- `pricing staging`: 743 rows
- `archive/rejected`: 0 rows

## Classification summary

All 743 rows were classified using explicit category, lookup completeness, and zero-value rules.

- `Mappable After Lookup Enrichment`: 511 rows (68.8%)
  - Rule: category is one of `Repair`, `Part`, `Device`, `Tool`, or `Accessory`, but the row has missing `Supplier` or `Manufacturer` values.
- `Requires Manual Review`: 232 rows (31.2%)
  - Rule: `Price == 0` and `Cost == 0` (both zero), indicating a likely non-priced reference item or unresolved data quality issue.
- `Automatically Mappable`: 0 rows (0.0%)
  - Rule: no rows were fully complete with canonical lookups and non-zero price/cost values in this raw extract.
- `Archive Only`: 0 rows (0.0%)
  - Rule: no rows had an unsupported category or explicit discard reason.
- `Reject`: 0 rows (0.0%)
  - Rule: no rows were rejected based on unsupported category mapping alone.

## Key migration implications

- Raw data must be normalized before canonical load.
- `SKU` values require type normalization and de-duplication.
- `Manufacturer` and `Supplier` references require enrichment or reconciliation for missing values.
- Zero-priced and zero-cost rows must be validated with business rules before ingestion.
- The raw import should be treated as a staging artifact whose provenance is preserved in canonical metadata.
- `Updated At` and `Created At` should be retained as source audit metadata, not as canonical transaction dates unless verified.
