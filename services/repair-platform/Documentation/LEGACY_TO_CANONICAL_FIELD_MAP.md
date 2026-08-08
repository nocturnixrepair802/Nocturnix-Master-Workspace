# Legacy to Canonical Field Map

This document maps fields from the legacy raw import workbook `Raw Import Data.xlsx` to canonical master catalog targets.
It also identifies fields that should be ignored or treated as staging metadata.

## Raw import field mapping

- `⬅ Return to Table of Contents` -> ignore
- blank placeholder columns -> ignore
- `Column1` -> ignore
- `SKU` -> legacy staging key: `Legacy SKU`
  - Normalize mixed numeric/string values to a consistent SKU string.
  - Do not treat `Legacy SKU` as an automatic canonical primary key because duplicate SKU occurrences exist.
  - Use as a lookup candidate and de-duplication grouping key in the staging pipeline.
- `Group` -> catalog classification field
  - Map to a normalized group or category dimension in catalog tables.
- `Category` -> record category field
  - Determine destination dataset based on legacy category:
    - `Repair` -> `master_services` / service staging candidate
    - `Part` -> `parts_catalog` candidate
    - `Device` -> `master_devices` candidate
    - `Tool` -> `tool_catalog` candidate
    - `Accessory` -> `accessories_catalog` candidate
    - physical stock records may instead target `inventory_items`
- `Type` -> canonical classification: `parts_catalog.Type` / `service_types.Service Type`
  - Map to canonical service or product type taxonomy.
- `Manufacturer` -> canonical lookup: `manufacturer_catalog.Manufacturer Name` / `Manufacturer ID`
  - Reconcile missing manufacturer references with the manufacturer catalog.
- `Name` -> catalog identity field: `parts_catalog.Name` / `inventory_items.Description`
- `Price` -> legacy monetary field: `Legacy Retail Price`
  - Preserve as a raw legacy retail price value.
  - Do not map directly to `pricing_rules`; keep formulas, margins, and policies in `pricing_rules` instead.
  - Future canonical targets may include supplier cost records, landed cost records, or price records.
- `Cost` -> legacy monetary field: `Legacy Cost`
  - Preserve as a raw legacy cost value.
  - Do not map directly to `pricing_rules`; keep pricing rules, formulas, and margin policy logic in `pricing_rules`.
  - Future canonical targets may include supplier cost records, landed cost records, or price records.
- `Stock` -> inventory field: `inventory_items.Stock`
- `Serial Number` -> inventory field: `inventory_items.Serial Number`
  - Likely optional staging metadata for serialized items.
- `Condition` -> inventory enumeration: `inventory_items.Condition`
  - Normalize values such as `New`, `Damaged`, and `Used`.
- `Tax Free` -> inventory/pricing flag: `inventory_items.Tax Free`
  - Normalize values to explicit boolean or controlled enumeration.
- `Bin` -> inventory location field: `inventory_items.Bin`
- `Supplier` -> canonical lookup: `supplier_catalog.Supplier Name` / `Supplier ID`
  - Reconcile missing supplier references and normalize supplier names.
- `Note` -> inventory/catalog note field: `inventory_items.Note`
  - Preserve as free-form staging commentary.
- `Updated At` -> canonical audit metadata: `audit.updated_at` or `source.updated_at`
  - Retain as source provenance, not as canonical effective date unless verified.
- `Created At` -> canonical audit metadata: `audit.created_at` or `source.created_at`
  - Retain as source provenance, not as canonical effective date unless verified.

## Staging identity fields

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

## Catalog fields vs inventory fields

### Catalog fields
- `identity`
- `manufacturer`
- `category`
- `type`
- `name` / `description`

### Inventory fields
- `stock`
- `serial number`
- `condition`
- `bin` / `location`
- `tax-free flag`

## Duplicate-resolution classifications

- `Exact Duplicate`
- `Same SKU / Same Item`
- `Same SKU / Conflicting Item`
- `Multi-Supplier Variant`
- `Multi-Condition Variant`
- `Requires Manual Review`

## Classification summary

All 743 rows were classified using explicit category, lookup completeness, and zero-value rules.

- `Automatically Mappable`: 0 rows (0.0%)
  - Rule: no rows were fully complete with canonical lookups and non-zero price/cost values in this raw extract.
- `Mappable After Lookup Enrichment`: 511 rows (68.8%)
  - Rule: category is one of `Repair`, `Part`, `Device`, `Tool`, or `Accessory`, but the row has missing `Supplier` or `Manufacturer` values.
- `Requires Manual Review`: 232 rows (31.2%)
  - Rule: `Price == 0` and `Cost == 0` (both zero), indicating a likely non-priced reference item or unresolved data quality issue.
- `Archive Only`: 0 rows (0.0%)
  - Rule: no rows were unsupported or explicitly marked for discard.
- `Reject`: 0 rows (0.0%)
  - Rule: no rows were rejected based on category mapping alone.

## Proposed destination counts

- `master_services`: 574 rows
- `parts_catalog`: 82 rows
- `master_devices`: 8 rows
- `tool_catalog`: 38 rows
- `accessories_catalog`: 1 row
- `inventory_items`: 40 rows
- `pricing staging`: 743 rows
- `archive/rejected`: 0 rows

## Zero-value migration decision matrix

- `Price = 0` and `Cost = 0` -> `Requires Manual Review`
  - Likely non-priced reference item, inactive/archive candidate, or missing data.
- `Price = 0` and `Cost != 0` -> `Requires Manual Review`
  - Could be a zero-cost service, a free item, or a data issue.
- `Price != 0` and `Cost = 0` -> `Mappable After Lookup Enrichment`
  - Likely missing supplier or cost metadata; requires reconciliation.
- `Price != 0` and `Cost != 0` -> `Mappable After Lookup Enrichment`
  - Candidate for canonical staging once lookups are resolved.
- `Price = 0` and `Cost = 0` for a known reference item -> `Archive Only`
  - If business rules confirm this is a legitimate non-priced reference item.
- `Price = 0` and `Cost = 0` for unknown row -> `Requires Manual Review`
  - Likely missing data or inactive/archive candidate.

## Unresolved business decisions

- Whether repair SKUs should be retained as legacy aliases or only as staging identifiers.
- Whether damaged and used physical items belong in inventory history or should be archived separately.
- Whether zero-cost repair services are valid service records or data quality artifacts.
- How supplier-less parts should be handled when supplier lookup data is missing.
- Whether duplicate supplier records represent valid sourcing alternatives or invalid duplicate inventory.

## Fields requiring special handling

- `SKU`
  - Mixed-type values require normalization to a consistent string representation.
  - Duplicate SKU groups must be de-duplicated and reconciled before canonical load.
- `Manufacturer`
  - Missing values in 93 rows require enrichment from a manufacturer lookup or business review.
- `Supplier`
  - Missing values in 650 rows indicate supplier data is not complete in the raw import.
  - A placeholder or lookup reconciliation process should be defined if supplier is required.
- `Price` / `Cost`
  - Zero values are common in the raw artifact and must be reviewed for business validity.
  - `Cost` contains string-encoded numeric values in a small number of rows.
- `Serial Number`, `Bin`, `Note`
  - Largely empty and should be treated as optional staging metadata.
- `Updated At` / `Created At`
  - Preserve as import source metadata; do not assume canonical transaction or effective dates without validation.

## Ignored fields

- `⬅ Return to Table of Contents`
- Blank placeholder header columns
- `Column1`

## Recommended import staging outcome

The staging pipeline should produce a normalized dataset with the following characteristics:

- canonical field names aligned to the master catalog document
- normalized SKU keys and vendor references
- numeric monetary values for `Price` and `Cost`
- reconciled lookup values for manufacturers and suppliers
- explicit source provenance metadata for auditability
- deduplicated records suitable for canonical ingestion
