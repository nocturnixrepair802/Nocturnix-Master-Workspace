# Master Compatibility Catalog V1 Validation Rules

## Authority

These rules implement
`Documentation/ADR/ADR-010-master-compatibility-governance.md` and the workbook
contract in `Documentation/MASTER_COMPATIBILITY_SPEC.md`.

## Schema and Workbook Checks

- Require the exact 15 worksheets in the documented order.
- Require unique worksheet names no longer than 31 characters.
- Require every expected table, globally unique table names, filters, and
  frozen header rows.
- Require every populated worksheet to contain an Excel Table.
- Require the primary table to have exactly the documented 31 columns in order.
- Reject pricing, cost, stock, quantity, supplier-cost, inventory, and final
  approval fields.
- Require a valid ZIP-based OOXML workbook that reopens successfully.

## Compatibility ID Checks

- Locate the canonical `Compatibility ID` header at runtime.
- Require canonical and generated IDs to match `^CMP\d{6}$`.
- Reject duplicate valid canonical IDs and duplicate generated IDs.
- Report malformed canonical values separately.
- Require generated IDs to be continuous, ordered, and nonoverlapping with
  canonical IDs.
- Require the first ID to follow the highest valid canonical ID, or be
  `CMP000001` for an ADR-010 empty namespace.
- Reconcile final ID as `first sequence + generated row count - 1`.

## Population and Ordering

- Recalculate the expected population from protected Master Devices, Master
  Services, and Master Parts inputs.
- Require one strongest supported candidate per target.
- Require deterministic ordering by Relationship Type, Device ID, target ID,
  Source Record Number, and family tie-breaker.
- Reject duplicate relationship keys.
- Reject any relationship derived from a source row listed in Duplicate
  Exclusions or whose source status is Rejected or Archived.

## Relationship Integrity

- Every Device ID resolves to Master Devices.
- Every Service ID resolves to Master Services.
- Every Part ID resolves to Master Parts.
- Device Family Code and manufacturer fields reconcile where populated.
- Service relationship types populate Service ID and leave Part ID blank.
- Part relationship types populate Part ID and leave Service ID blank.
- Family relationships populate Device Family Code and leave Device ID blank.
- Model relationships populate Device ID.
- Variant relationships populate Device ID and Device Variant.
- Names in relationship rows equal their referenced lookup rows.

## Evidence Safeguards

- Every Proposed relationship has nonblank Evidence Type, Evidence Source, and
  Evidence Detail.
- Evidence Type is one of the documented controlled values.
- Every inferred or family relationship requires manual review and is inactive.
- No generated relationship is Confirmed.
- No generated Review Status is Approved or Ready for Approval.
- Family-only evidence cannot produce a model or variant relationship.
- Generic target names alone cannot produce precise compatibility.
- Weak similarity, manufacturer-only agreement, and a generic `phone` token
  are never sufficient.

## Duplicate and Queue Checks

- Relationship uniqueness uses Relationship Type, Device ID or family code,
  target ID, and Device Variant.
- Different evidence or levels are not silently merged.
- Every pending relationship appears exactly once in the Family, Model, or
  Variant queue matching its Compatibility Level.
- Every unresolved expected candidate appears exactly once in Unresolved
  Review.
- Queue keys reconcile to primary relationship keys; no queue contains a
  duplicate.

## Defined Names and Data Validation

- Require all 12 `DV_*` names documented in the specification.
- Require workbook scope and the documented lookup destination.
- Require controlled primary fields to use only defined-name list formulas.
- Reject direct cross-sheet formulas and hard-coded list validation.
- Reopen and revalidate every defined name and validation destination.

## Protected Inputs and Output Safety

- Hash the canonical workbook, Master Devices, Master Services, Master Parts,
  Master Pricing, and deduplication proposal before and after generation.
- Require unchanged hashes. No source workbook may be saved.
- Normalize aware datetimes to naive UTC before Excel persistence.
- Write to a temporary sibling `.xlsx`.
- Validate required OOXML members and fully validate the temporary workbook.
- Atomically replace the final output only after all checks pass.
- Remove the temporary output on failure.
- The validator returns a descriptive failure for missing, empty, corrupt, or
  structurally invalid output.

## Canonical Import Prohibition

A validation pass does not authorize writes to `35 Compatibility Matrix`, any
canonical table, any protected catalog, pricing, inventory, or an engine.
Canonical import requires a separate approved migration with backup, business
approval, validation, and rollback controls.
