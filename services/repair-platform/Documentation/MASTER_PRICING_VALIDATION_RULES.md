# Master Pricing Catalog V1 Validation Rules

## Protected Inputs

- Require Master Services, Labor Standards, deduplication proposal, and canonical
  database exactly once in the protected path collection.
- Require each file to exist, be nonempty, and pass `zipfile.is_zipfile`.
- Open inputs read-only; open the canonical `.xlsm` with `keep_vba=True`.
- Hash every protected input before reading and after reopened output validation.
- Store original SHA-256 values in `12 - Import Metadata`; fail on any change.
- Never call `save()` on an input workbook.

## Schema and Workbook Checks

- Require the exact 13-sheet order and titles from the specification.
- Require unique worksheet titles no longer than 31 characters.
- Require the exact 47-column Pricing Records schema.
- Require the documented Excel Table on every sheet and unique table names.
- Require filters, frozen row 1, and no merged cells in tables.
- Reopen the generated workbook and repeat structural checks.
- Require date, percentage, and currency formats on their documented columns.
- Require conditional formatting for pending/research statuses, prohibited
  approval states, missing inputs, and review queue entries.

## Identity and Population Checks

- Enforce ADR-007 as the Pricing Record ID namespace authority.
- Treat no `Pricing Record ID` column or no valid canonical `PRC######` values
  as an approved empty namespace beginning at `PRC000001`.
- Report malformed canonical values and exclude them from sequence calculation.
- Reject duplicate valid canonical IDs.
- Require every generated ID to match `^PRC\d{6}$`, be unique, avoid existing
  IDs, and form one continuous sequence.
- Require the first ID to equal the highest existing valid ID plus one when
  valid canonical IDs exist.
- Require the first ID to equal `PRC000001` only when the namespace is empty.
- Require the final numeric ID to reconcile to the generated row count.
- Require exactly 314 pricing rows, one per eligible Master Service, in source
  order.
- For the current empty namespace and 314-row source, require the expected range
  `PRC000001` through `PRC000314`.
- Require Service IDs to match `^SVC\d{6}$`, remain unchanged and unique, with
  no missing or extra source Service IDs.
- Require unique positive Source Record Numbers.
- Reject services marked Rejected or Archived.
- Reject any Source Record Number listed in proposal
  `02 - Duplicate Exclusions`.

## Source and Relationship Checks

Require exact source preservation for Service ID, Legacy Service SKU, Service
Name, manufacturer ID/name, device-family code/name, Legacy Pricing Status,
Legacy Retail Price, Legacy Cost, Labor Standard ID, source record number,
source workbook, source worksheet, Created At, and Updated At.

- Every populated Labor Standard ID must resolve once in the labor catalog.
- Standard Labor Minutes and Labor Rate Tier must equal the referenced labor row.
- Blank labor mapping requires `Labor Mapping Required`.
- Labor Rate and Labor Cost may not be inferred from a labor tier or legacy
  workbook example.
- Manufacturer and device-family pairs must equal the Service reference,
  including intentional blanks.

## Monetary and Blank/Zero Checks

- Parse monetary and percentage fields with `Decimal(str(value))`; reject Boolean,
  nonfinite, or invalid populated calculated inputs.
- Reject negative monetary values.
- Preserve legacy numeric zero as zero and blank as blank.
- Preserve invalid legacy monetary text for review; never coerce it to zero.
- Do not treat zero Repair cost as verified cost or as a data-quality failure.
- Require all generated cost-component fields to remain blank.
- Require Total Internal Cost blank if any required component is blank.
- Require Recommended Price and Final Customer Price blank for every V1 row.
- Require Minimum Approved Price, Maximum Approved Price, Effective Date, and
  Expiration Date blank in generated V1.
- When later populated, require percentages from 0 through 1 and expiration not
  before effective date.
- Reject formulas in legacy observations, calculated fields, or final fields.

## Status Checks

- Require both `Legacy Pricing Status` and `Pricing Status`.
- Require Legacy Pricing Status to equal the Master Services source observation.
- Require Pricing Status to follow the governed pricing lifecycle without
  overwriting Legacy Pricing Status.
- Require Pricing Status, Pricing Method, Review Status, and Pricing Confidence
  to be controlled values.
- Derive initial Pricing Status in this order: missing labor, unresolved cost,
  unresolved market, ready for calculation.
- Require `Not Yet Determined`, `Pending Review`, and `Unassessed` defaults.
- Prohibit generated `Ready for Approval` and `Approved`.
- Prohibit `Ready for Pricing Calculation` while any required cost or market
  input is unresolved.
- Require currency blank until confirmed.

## Lookup and Defined-Name Checks

Require workbook-scoped names:

- `DV_PricingStatuses`
- `DV_PricingMethods`
- `DV_Currencies`
- `DV_ServiceIDs`
- `DV_LaborStandardIDs`
- `DV_LaborRateTiers`
- `DV_MarginTargets`
- `DV_RegionalMarkets`
- `DV_ReviewStatuses`
- `DV_PricingConfidenceValues`

Each name must be unique, resolve to its documented table column, and be used by
the intended Pricing Records DataValidation. Reject direct cross-sheet list
ranges and hard-coded lists. Confirm populated values belong to the referenced
lookup.

## Review Queue and Provenance

- Require one queue row for every unresolved pricing record.
- Require exact queue identity/status agreement with Pricing Records.
- Require Missing Inputs and Required Action to be nonblank.
- Require blank Reviewer Notes initially.
- Verify Import Metadata paths, source worksheets, row counts, ID findings,
  hashes, batch ID, and generation boundary.
- Ensure no source row is lost, duplicated, or reintroduced from exclusions.

## Approval and Import Prohibition

- A passing validation means only that the review workbook is structurally
  correct and traceable.
- It does not approve a cost, margin, price, publication, quote, or import.
- The scripts must not write to the canonical database, source workbooks,
  PricingEngine, QuoteEngine, or runtime application code.
- Canonical import and pricing publication require separately approved,
  reversible workflows.
- Initial Pricing Record IDs identify draft review rows only. No Final Customer
  Price is approved.
