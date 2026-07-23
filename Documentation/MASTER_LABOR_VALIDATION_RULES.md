# Master Labor Catalog V1 Validation Rules

## Authority

These rules implement
`Documentation/ADR/ADR-011-master-labor-standards-governance.md` and the
workbook contract in `Documentation/MASTER_LABOR_SPEC.md`.

## Schema and Workbook Checks

- Require the exact 14 worksheets in documented order.
- Require unique worksheet names no longer than 31 characters.
- Require the expected table on every sheet, globally unique table names,
  filters, and frozen header rows.
- Require `tblMasterLaborCatalog` to contain exactly the documented 31 columns
  in order.
- Reject rate, cost, price, payroll, schedule, time-clock, inventory, and
  automatic-approval fields.
- Require a valid ZIP-based OOXML workbook, required OOXML members, and
  successful reopen.

## Labor Standard ID Checks

- Treat source `Labor ID` values such as `NSLC-001` as legacy aliases and
  preserve them exactly in Legacy Labor ID.
- Inspect only an explicitly governed `Labor Standard ID` column for existing
  `LAB######` identifiers.
- Require every populated governed and generated ID to match `^LAB\d{6}$`.
- Report malformed values only from the governed column and reject duplicate
  or out-of-order governed IDs.
- Require generated IDs to be unique, strictly ordered, continuous, and
  nonoverlapping with protected IDs.
- Require the first generated ID to follow the highest protected ID, or be
  `LAB000001` when ADR-011 authorizes the absent or empty governed namespace.
- Reconcile the final generated ID to first sequence plus row count minus one.

## Population and Provenance

- Recalculate expected rows from the protected Labor Standards worksheet.
- Require deterministic ordering by Source Record Number and source row.
- Require each source record exactly once; reject duplicate source lineage.
- Require every source Legacy Labor ID to be nonblank and unique.
- Require every generated Legacy Labor ID to equal its source observation
  exactly; do not apply the governed ID regex to legacy aliases.
- Require Labor Name and all provenance fields.
- Require Import Batch `MASTER-LABOR-V1-REVIEW`.
- Require copied values to equal explicit source values under documented field
  aliases; values absent from the source remain blank except generated
  governance fields.

## Labor Relationships

- Standard Minutes, when populated, is a positive whole number.
- Minimum Minutes, when populated, is a nonnegative whole number.
- Maximum Minutes, when populated, is a positive whole number.
- Require `Minimum Minutes <= Standard Minutes <= Maximum Minutes` for every
  populated comparable pair.
- Controlled lookup values resolve exactly when populated.
- Requirement flags contain only Yes, No, or blank.
- Generated Review Status is Pending Review and generated Reviewer is blank.
- No row is automatically Approved or Ready for Approval.
- Labor tier, skill, difficulty, warranty, tools, certification, and minutes
  may not be synthesized from another field.

## Defined Names and Data Validation

- Require all 11 documented workbook-scoped `DV_*` names.
- Require each name to resolve to its documented lookup column.
- Require every governed primary-field list validation to use only its defined
  name.
- Reject direct cross-sheet formulas and hard-coded comma-separated lists.
- Reopen and revalidate defined names and validation destinations.

## Protected Hashes and Output Safety

- Generator hashes the protected Labor Standards source before and after work.
- Mapping review generator hashes Master Services and Master Labor before and
  after work.
- Validator compares current protected-source hashes with Import Metadata.
- Reject a changed or missing protected source.
- Write each output first to a temporary sibling `.xlsx`.
- Refuse to proceed when a stale temporary output exists.
- Validate the temporary workbook, atomically replace the target only after a
  passing validation, and require temporary output cleanup.
- Never save an input workbook.

## Reopened and OOXML Integrity

- Reopen the persisted workbook with formulas preserved.
- Recheck worksheets, tables, headers, row counts, defined names, validations,
  IDs, relationships, provenance, and metadata after reopen.
- Require `[Content_Types].xml`, `_rels/.rels`, `xl/workbook.xml`,
  `xl/_rels/workbook.xml.rels`, and every referenced worksheet and table member.
- Reject a corrupt, non-OOXML, macro-bearing, or externally linked review
  workbook.

## Labor Mapping Review Rules

- Require exactly one row for every Service ID and no extra or duplicate row.
- Preserve Service ID, Service Name, and Current Labor Standard exactly.
- Suggested Labor Standard is blank or resolves to a governed `LAB######`
  Master Labor ID.
- An `NSLC-*` Legacy Labor ID may appear only as supporting evidence and is
  never the governed suggested mapping.
- Match Score and Margin are bounded from 0 through 1.
- Evidence is nonblank when a suggestion is populated.
- Review Status is always Pending Review on generation.
- No mapping is marked Approved and Master Services is never modified.

## Exit Contract

A validator exits zero only when every check passes. Failures are reported to
stderr and exit nonzero. A passing result authorizes review only, not canonical
import.
