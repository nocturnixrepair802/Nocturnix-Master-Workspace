# Master Devices Catalog V1 Validation Rules

These rules implement the identity and schema decision accepted by ADR-009.

## Input and Protection

1. Every protected input exists, is nonempty, and is a valid ZIP-based Office
   workbook.
2. Canonical source is opened read-only with `keep_vba=True`.
3. SHA-256 hashes for proposal, Master Services, Master Parts, Master Pricing,
   and canonical database are unchanged before and after generation.
4. No protected workbook is saved.

## Source Population and Provenance

1. Proposal `01 - Retained` contains required headers.
2. Exactly 46 rows currently have `Record Category = Device`.
3. Each generated row maps to one unique retained Source Record Number.
4. Generated source order is ascending.
5. No source row is lost, duplicated, or added.
6. Source workbook, worksheet, timestamps, SKU, name, note, and monetary
   observations reconcile to the proposal.
7. No row from `02 - Duplicate Exclusions` is introduced.

## Structure

1. Workbook has exactly 15 worksheets in the documented order.
2. Worksheet titles are unique and at most 31 characters.
3. `01 - Master Devices` has exactly the documented 48 columns.
4. Every worksheet has its documented Excel Table.
5. Table names are unique and table references are valid.
6. Filters and frozen header rows exist.
7. No table contains merged cells.

## Device ID

1. Canonical worksheet `32 Devices` and exact `Device ID` header exist.
2. Valid canonical IDs, when present, match `^DEV\d{6}$`; an empty valid
   namespace begins at ADR-009's `DEV000001`.
3. Duplicate valid canonical IDs fail.
4. Malformed populated IDs are reported and excluded from sequence math.
5. Every generated ID matches `^DEV\d{6}$`.
6. Generated IDs are unique and do not collide with canonical IDs.
7. IDs form one continuous sequence.
8. First generated ID equals highest valid canonical ID plus one.
9. Final generated ID equals first plus generated row count minus one.
10. ID order follows ascending Source Record Number.

## Lookup Integrity

1. Manufacturer ID resolves to exactly one Manufacturer Name.
2. Device Family Code resolves to exactly one Device Family Name.
3. Blank Manufacturer ID requires `Pending Manufacturer Review`.
4. Blank Device Family Code requires `Pending Family Review` unless
   Manufacturer is also unresolved and the more restrictive
   `Pending Manufacturer Review` applies.
5. A populated Manufacturer ID or Family Code must agree with its displayed
   name.
6. Product Line values must be present in the product-line lookup.
7. Any populated series, form factor, OS family, network type, or currency must
   exist in its controlled lookup.

## Defined Names and Data Validation

1. Every documented defined name exists and resolves to a valid range.
2. Each required field uses the correct defined name.
3. List formulas are exactly `=<defined name>`.
4. Direct cross-sheet validation formulas are prohibited.
5. Data validation covers all generated data rows.

## Conservative Mapping

1. Generated Status is `Draft`; no row is Approved or Ready for Approval.
2. V1 boolean defaults match the specification.
3. Model, variant, generation, release year, form factor, OS, network, storage,
   memory, color, region, carrier, and currency remain blank.
4. Compatibility, service mapping, and parts mapping remain pending.
5. Reviewer and approval dates remain blank.
6. Identity and relationship review tables contain every generated Device ID
   exactly once and preserve device order.

## Monetary Values

1. Legacy Retail Price and Legacy Cost use decimal-compatible numeric values.
2. Blank and zero remain distinct.
3. Negative values fail.
4. No final pricing or calculated cost field exists.

## Output Safety

1. All workbook-bound aware datetimes are converted to naive UTC; aware time
   values have `tzinfo` removed while preserving wall-clock value.
2. Output is saved to a sibling temporary path.
3. Temporary output is a valid OOXML ZIP before reopened validation.
4. Final output is replaced atomically only after all checks pass.
5. Failure removes the temporary file and leaves no partial final replacement.
6. Independent validator rejects missing, empty, or invalid ZIP output with a
   descriptive rerun instruction.

## Import Boundary

A passing result is a review artifact only. It does not approve or perform
canonical import, customer-device creation, inventory creation, compatibility,
service mapping, parts mapping, or pricing publication.
