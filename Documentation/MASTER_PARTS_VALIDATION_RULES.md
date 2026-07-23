# Master Parts Catalog V1 Validation Rules

ADR-008 is the authority for Part ID allocation and the 50-column schema.

## Protected Inputs

- Require proposal, Master Services, Master Pricing, and canonical database once.
- Require existence, positive size, valid ZIP container, and required worksheets.
- Open all inputs read-only; canonical `.xlsm` uses `keep_vba=True`.
- Hash inputs before reading and after reopened output validation.
- Store paths and initial SHA-256 values in Import Metadata.
- Never save an input workbook.

## Workbook and Schema Checks

- Require exactly 15 worksheets in documented order.
- Require unique titles no longer than 31 characters.
- Require exact 50-column Master Parts schema.
- Require every documented Excel Table and unique table names.
- Require every populated worksheet to be represented by its table.
- Require frozen row 1, filters, no table merges, semantic number formats, and
  required conditional formatting.
- Reopen and repeat checks before publication.

## Population and Provenance

- Filter proposal Retained rows to exact Record Category `Part`.
- Recalculate and require the current expected count of 48.
- Require one output row per retained Part and no non-Part rows.
- Preserve ascending Source Record Number order.
- Require unique positive source numbers and no omissions.
- Reject any source row listed in Duplicate Exclusions.
- Preserve Source Workbook, Source Worksheet, timestamps, and batch metadata.

## Part Identity

- Inspect exact `Part ID` columns in canonical `39.4 Repair Parts` and `41 Parts`.
- Accept only IDs matching `^PRT\d{6}$`.
- Reject duplicate valid canonical IDs.
- Report malformed populated IDs and exclude them from sequence math.
- With existing IDs, begin at highest valid ID plus one.
- With no valid IDs, apply ADR-008 and begin at `PRT000001`.
- Require generated format, uniqueness, continuity, no overlap, first-ID logic,
  final-ID reconciliation, and source-order assignment.
- For the current empty namespace and 48 rows, require `PRT000001` through
  `PRT000048`.
- Never use Legacy Part SKU as the canonical key.

## Source Preservation

Require type-aware equality to retained source for Legacy Part SKU, Part Name,
Part Display Name, Part Description when sourced from note, Part Category, Part
Type, Manufacturer Name, Supplier Name, Legacy Retail Price, Legacy Cost,
Condition, Reviewer Notes, Source Record Number, Source Workbook, Source
Worksheet, Created At, and Updated At.

Blank and zero are different. Text timestamps remain text. Aware datetimes are
converted to naive UTC only at the Excel persistence boundary.

## Relationship Checks

- Populated Manufacturer ID must resolve to Manufacturer Name.
- Populated Device Family Code must resolve to Device Family Name.
- Populated Device ID must resolve to Device Name and its family/manufacturer.
- Populated Supplier ID must resolve to Supplier Name.
- Lookup IDs must exist in both output lookup tables and authoritative sources.
- Missing manufacturer or device relationships require the documented pending
  status.

## Compatibility Checks

- Require one Compatibility Review row per Master Part in identical order.
- Require identity/name fields to match Master Parts.
- Require missing inputs and required action for unresolved rows.
- Device Family Only requires a populated family and blank device.
- Device Specific requires a valid Device ID.
- Pending compatibility may not be marked Approved.
- Do not infer or write canonical Compatibility Matrix records.

## Sourcing Checks

- Require one Sourcing Review row per Master Part in identical order.
- Preserve observed Supplier Name and Legacy Cost.
- Preferred Supplier remains No unless separately reviewed.
- Supplier Part Number remains blank without evidence.
- Missing supplier routes to Supplier Unknown or Pending Sourcing Review.
- No landed-cost or selling-price calculation is permitted.

## Monetary Checks

- Parse populated monetary values with `Decimal(str(value))`.
- Preserve invalid legacy text for review but reject negative numeric values.
- Preserve numeric zero and blank distinctly.
- Do not round or calculate new amounts.
- Currency remains blank without confirmed policy.
- Reject final cost, landed cost, markup, margin, and final customer-price fields.

## Status Checks

- Require controlled Part, Review, Compatibility, Sourcing, Cost, and Pricing
  statuses and controlled Yes/No flags.
- Prohibit generated Approved and Ready for Approval values.
- Missing manufacturer routes to Pending Manufacturer Review.
- Missing device applicability routes to Pending Device Mapping or Pending
  Compatibility Review.
- Missing supplier/cost routes to sourcing or cost review.
- No row with unresolved required relationships may be Ready for Approval.

## Defined Names and Data Validation

Require every `DV_*` name documented in the specification, workbook scope,
correct lookup target, and use by the intended Master Parts field. Reject direct
cross-sheet formulas and hard-coded governed lists.

## Output Safety

- Convert aware datetimes to UTC and remove timezone before writing.
- Preserve naive datetimes, dates, blanks, and text timestamps.
- Save to `Nocturnix_Master_Parts_Catalog_v1.tmp.xlsx`.
- Validate the temporary workbook fully.
- Atomically replace the final path only after success.
- Close the workbook and delete temporary output on failure.
- The independent validator rejects a missing, empty, corrupt, or incomplete
  Excel ZIP with a descriptive rerun message.

## Import Prohibition

A passing result does not authorize canonical import, inventory updates,
purchasing, supplier approval, compatibility approval, cost approval, or final
pricing. Those require separate governed workflows.
