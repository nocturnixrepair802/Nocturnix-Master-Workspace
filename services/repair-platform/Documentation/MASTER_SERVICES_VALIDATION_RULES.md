# Master Services Catalog Validation Rules

## Schema Checks

- Require all 16 worksheets in the specified order.
- Require unique worksheet names no longer than 31 characters.
- Require the exact 45-column Master Services schema.
- Require `tblMasterServicesCatalog` and unique Excel Table names.
- Require every populated worksheet range to be represented by an Excel Table.
- Reject final customer price, final price, and final cost columns.

## Identity Checks

- Require exactly 314 proposed services.
- Read existing Service IDs from `Data/Nocturnix_Master_Database.xlsm`,
  worksheet `34 Master Services`; fail rather than guess if it cannot be read.
- Require every generated Service ID to be nonblank, unique, and formatted as
  `SVC######` with regex `^SVC\d{6}$`.
- Report malformed existing IDs but exclude them from sequence calculation.
- Require no generated ID to exist in the authoritative worksheet.
- Require one continuous generated sequence in ascending Source Record Number
  order, beginning at the highest valid existing ID plus one.
- Require the final ID to equal the first generated ID plus generated row count
  minus one. With the currently confirmed highest ID `SVC000075`, the expected
  314-row review range is `SVC000076` through `SVC000389`; do not hard-code that
  start for future runs.
- Require unique Source Record Numbers.
- Treat Legacy Service SKU only as a preserved alias/reference.
- Do not assign a Service ID to rejected or archived source records.

## Lookup Checks

- Validate Manufacturer ID, Device Family Code, Service Category ID, Repair Type
  ID, Labor Standard ID, Labor Tier, Repair Difficulty, Skill Level, Turnaround
  Time, and Default Warranty against their workbook lookup tables.
- Permit blank Manufacturer, Device Family, and labor fields only when the row's
  review status identifies the unresolved mapping.
- Require controlled `Yes` or `No` values for all Boolean-style flags.

## Labor Checks

- Every populated Labor Standard ID must exist in both the output lookup and the
  protected labor catalog.
- Standard, Minimum, and Maximum Minutes, Labor Tier, Repair Difficulty, and
  Skill Level must equal the referenced protected labor row.
- Standard Minutes must be positive when Labor Standard ID is populated.
- Require `Minimum Minutes <= Standard Minutes <= Maximum Minutes`.
- Leave labor fields blank and set `Pending Labor Mapping` when no reliable match
  exists; never create a duration to satisfy validation.
- Require the exact labor-audit schema documented in the specification.
- Require one audit row per service in the same Service ID and Source Record
  Number order.
- Reject missing, duplicate, reordered, blank, or invalid audit Service IDs.
- Require Legacy Service Name to equal Service Name.
- Require `Score Margin = Match Score - Second Best Score`.
- Require nonblank Match Evidence and a controlled Mapping Result.
- Require mapped rows to exceed the `0.82` threshold and `0.03` margin.
- Require mapped values to equal both the Master Services row and protected labor
  row.
- Require unresolved rows to have blank Labor Standard ID and mapped fields.
- Verify the labor-audit digest stored in Import Metadata so changed audit values
  fail validation.

## Pricing Checks

- Permit only Pending Pricing Review, Legacy Price Review, No Pricing Exceptions,
  and Archive Candidate.
- Preserve Legacy Retail Price and Legacy Cost observations.
- Do not require a positive Repair cost.
- Do not calculate, infer, approve, or publish final pricing.
- Reject any final price or final cost field.

## Provenance Checks

- Reconcile every service to a retained Repair row by Source Record Number.
- Require Legacy Service SKU to equal the retained source observation.
- Require exactly the retained Repair source population.
- Reject any row listed in `02 - Duplicate Exclusions`.
- Require unique source-row provenance.

## Review-Status Checks

- Permit only controlled review statuses.
- Unresolved conflicts must remain `Pending Review` and `Draft`.
- Unmatched labor records must be `Pending Labor Mapping`.
- Rejected and archived source rows must not receive Service IDs.

## Workbook Checks

- Reopen the output successfully after generation.
- Require filters, frozen header rows, Excel Tables, and unique table names.
- Require the exact table-name contract for all 16 worksheets.
- Require controlled-value data validations on the specified Master Services
  fields.
- Require all list validations to reference the documented workbook-defined
  names and reject direct cross-sheet formulas.
- Require currency, minute, and date formats on their respective columns.
- Require no blank value in a field classified as required by the data dictionary.

## Protected-File Hash Checks

The generator hashes the raw import, staging preview, deduplication proposal,
labor catalog, and canonical database before generation and again after output
validation. It embeds the original hashes in Import Metadata. The independent
validator recalculates and compares each hash. Any change is a failure.

## Canonical Import Prohibition

Neither script writes to the canonical database or performs an import. A passing
validation result means only that the standalone proposal satisfies this package
contract. It does not authorize canonical ingestion or pricing approval.
