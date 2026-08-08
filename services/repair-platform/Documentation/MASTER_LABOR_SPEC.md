# Master Labor Catalog V1 Specification

## Authority and Purpose

This specification implements
`Documentation/ADR/ADR-011-master-labor-standards-governance.md`.
Master Labor Catalog V1 is the governed review catalog for repair labor
standards referenced by Services.

Planned review outputs:

- `D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Labor_Catalog_v1.xlsx`
- `D:\Business Portal\300_Pricing\Working\Labor_Mapping_Review_v1.xlsx`

Neither output is a canonical import. The scripts never save an input workbook
or update Master Services.

## Scope and Boundary

A labor standard describes a repair activity, its applicability, explicitly
observed duration bounds, skill expectations, and task requirements. It does
not describe technician availability, scheduling, payroll, clock time, labor
rate, labor cost, customer price, or completed work.

The generator copies only explicit source observations. Blank source facts
remain blank. It does not infer labor, minutes, tiers, skills, difficulty,
warranty, tools, certification, or approval.

## Protected Inputs and Source Precedence

All inputs are read-only and protected by SHA-256 before and after generation:

1. `D:\Business Portal\300_Pricing\Labor Standards\Nocturnix_Standard_Labor_Catalog_v1.xlsx`
   supplies source labor observations and legacy identifiers such as
   `NSLC-001`. Its `Labor ID` column is legacy lineage, not the governed
   namespace.
2. `D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Services_Catalog_v1.xlsx`
   supplies Service records only to the mapping-review generator.

The mapping artifact also protects the generated Master Labor workbook. A
conflict remains unresolved; no weaker observation overwrites an explicit
source value.

## Identity and Allocation

The canonical identifier is `LAB######`, matching `^LAB\d{6}$`.
At runtime the catalog generator:

- requires a nonblank, unique source `Labor ID` or `Legacy Labor ID` for every
  protected source row and preserves it exactly as `Legacy Labor ID`;
- inspects only an explicitly governed `Labor Standard ID` column for existing
  `LAB######` identifiers;
- never validates an `NSLC-*` legacy alias against the governed regex;
- reports malformed populated values only from the governed column and rejects
  duplicate governed IDs or governed IDs not strictly increasing in source
  row order;
- starts at `LAB000001` when the governed column is absent or empty under the
  ADR-011-authorized empty namespace;
- otherwise starts after the highest existing valid ID;
- assigns IDs in ascending Source Record Number and source-row order;
- requires a continuous generated sequence; and
- rejects overlap with the protected namespace.

Legacy Labor ID preserves the source identifier, including `NSLC-*`, exactly
as lineage. A proposed governed Labor Standard ID identifies a review row only.
Assigning it does not approve a Service mapping or canonical import.

## Workbook Contract

The primary schema has exactly 31 columns in the order documented in
`MASTER_LABOR_DATA_DICTIONARY.md`.

| Order | Worksheet | Excel Table |
|---:|---|---|
| 1 | 00 - Instructions | `tblMasterLaborInstructions` |
| 2 | 01 - Labor Standards | `tblMasterLaborCatalog` |
| 3 | 02 - Repair Categories | `tblLaborRepairCategories` |
| 4 | 03 - Repair Types | `tblLaborRepairTypes` |
| 5 | 04 - Device Families | `tblLaborDeviceFamilies` |
| 6 | 05 - Manufacturers | `tblLaborManufacturers` |
| 7 | 06 - Labor Tiers | `tblLaborTiers` |
| 8 | 07 - Skill Levels | `tblLaborSkillLevels` |
| 9 | 08 - Difficulty | `tblLaborDifficulties` |
| 10 | 09 - Warranty Options | `tblLaborWarrantyOptions` |
| 11 | 10 - Review Queue | `tblLaborReviewQueue` |
| 12 | 11 - Validation Summary | `tblMasterLaborValidation` |
| 13 | 12 - Revision History | `tblMasterLaborRevisionHistory` |
| 14 | 13 - Import Metadata | `tblMasterLaborImportMetadata` |

Worksheet names are unique and no longer than 31 characters. Every worksheet
contains exactly one table, filters, and a frozen header row.

## Defined Names

All list validations use workbook-scoped defined names:

- `DV_LaborRepairCategories`
- `DV_LaborRepairTypes`
- `DV_LaborDeviceFamilies`
- `DV_LaborManufacturers`
- `DV_LaborTiers`
- `DV_LaborSkillLevels`
- `DV_LaborDifficulties`
- `DV_LaborWarrantyOptions`
- `DV_LaborReviewStatuses`
- `DV_LaborConfidence`
- `DV_YesNo`

Direct cross-sheet validation formulas and hard-coded comma-separated governed
lists are prohibited.

## Review Lifecycle

Review Status values are Pending Review, Pending Evidence Review, Ready for
Approval, Approved, Rejected, and Archived. Generated rows are always Pending
Review. Confidence values are Unassessed, Low, Medium, and High. Confidence is
evidence quality, not approval.

Rows with missing required evidence or invalid relationships are presented to
the review queue; the queue does not supply an outcome.

## Labor Mapping Review

`Labor_Mapping_Review_v1.xlsx` contains exactly one row per Master Service with:

Service ID, Service Name, Current Labor Standard, Suggested Labor Standard,
Confidence, Evidence, Match Score, Margin, and Review Status.

The generator preserves the current mapping as an observation. A current
`NSLC-*` value may resolve through the preserved Legacy Labor ID as supporting
evidence, but Suggested Labor Standard is always blank or a governed
`LAB######` ID. Candidate scoring uses only populated service and labor text
fields. A suggestion may be shown for review, but Review Status is always
Pending Review and the script does not write to Master Services. Blank or
insufficient evidence produces a blank suggestion.

## Ownership and Limitations

- Labor policy and approval: Operations and Labor Planning.
- Repair capability, skill, and certification review: Repair Engineering.
- Service-to-labor mapping approval: Repair Engineering and Operations.
- Workbook construction and protected-file controls: Data Engineering.
- Payroll, scheduling, time tracking, labor rates, pricing, and canonical
  migration remain outside this version.

A passing validator establishes integrity of a review artifact only.
