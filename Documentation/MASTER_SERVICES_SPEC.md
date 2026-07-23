# Master Services Catalog v1 Specification

## Purpose

Define a standalone, proposed canonical Master Services catalog for review before
any separately approved import into `Data/Nocturnix_Master_Database.xlsm`.

## Scope

The package contains 314 retained legacy Repair records, proposed `SVC######`
identities, lookup tables, conservative labor mappings, legacy pricing
observations, validation results, revision history, and import metadata. It does
not calculate prices or costs and does not modify an authoritative workbook.

## Source Precedence

1. `Documentation/MASTER_CATALOG_ARCHITECTURE.md` defines canonical ownership and
   architectural boundaries.
2. `Documentation/ADR/ADR-006-canonical-master-catalog-baseline.md` establishes
   that architecture as authoritative.
3. The deduplication proposal's `01 - Retained` sheet supplies reviewed legacy
   Repair candidates and source provenance.
4. The labor catalog supplies labor standards, tiers, difficulty, skill, and
   warranty reference data.
5. The canonical database supplies existing lookup identities. It is read-only.
6. Legacy values are preserved as source observations and never override an
   authoritative canonical value without review.

## Service Identity Rules

- Read all existing Service IDs from `Data/Nocturnix_Master_Database.xlsm`,
  worksheet `34 Master Services`, at runtime.
- Accept existing IDs for sequence calculation only when they match
  `^SVC\d{6}$`; report malformed values and exclude them from the calculation.
- Assign new IDs in ascending Source Record Number order using the next number
  after the highest valid existing ID.
- Never reuse or renumber an existing Service ID and never guess a start value
  when the authoritative worksheet cannot be read.
- The current confirmed highest existing ID is `SVC000075`, so the expected
  314-row draft range is `SVC000076` through `SVC000389`. This is a review
  baseline, not a hard-coded permanent start.
- Service IDs are unique and nonblank in the output artifact.
- `Legacy Service SKU` is an alias/reference and never the canonical key.
- Preserve the legacy SKU and source record number exactly.
- Do not create a service for a rejected, archived, or duplicate-exclusion row.
- Distinct reviewed services sharing a legacy SKU receive distinct Service IDs.
- Unresolved conflicts remain `Draft` and `Pending Review`.

## Labor Mapping Rules

The catalog generator's embedded preliminary mapping derives Device Category
from legacy type/group/name text, compares the legacy group/name/type values to
the labor Service, and uses Manufacturer agreement as supporting evidence.

The standalone Master Labor Mapping Engine V1 rescoring audit uses
Manufacturer, Device Family, Repair Type, Service Name similarity, Device Model
keywords, Labor Category, Repair Difficulty, and Skill Level. Candidate ordering
is deterministic. Both workflows accept a match only when its score is greater
than `0.82` and its score margin is greater than `0.03`. Materially tied rows are
`Ambiguous`; lower-scoring rows are `Pending Labor Mapping`.

When a reliable match exists, the generator copies Labor Standard ID, Standard,
Minimum, and Maximum Minutes, Labor Tier, Repair Difficulty, and Skill Level.
When evidence is insufficient, Labor Standard ID and time fields remain blank,
the service is preserved, and Review Status becomes `Pending Labor Mapping`.
The generator never invents a labor duration.

The embedded and standalone audit tables use this exact 13-column schema:

1. Source Record Number
2. Service ID
3. Legacy Service Name
4. Labor Standard ID
5. Match Score
6. Second Best Score
7. Score Margin
8. Match Evidence
9. Mapping Result
10. Mapped Minutes
11. Mapped Labor Tier
12. Mapped Difficulty
13. Mapped Skill Level

Unresolved audit rows leave Labor Standard ID and all mapped fields blank.

## Workbook Contract

The generated Master Services workbook contains these 16 worksheets in this
exact order:

1. `00 - Instructions`
2. `01 - Master Services`
3. `02 - Service Categories`
4. `03 - Repair Types`
5. `04 - Device Families`
6. `05 - Manufacturers`
7. `06 - Labor Standards`
8. `07 - Labor Tiers`
9. `08 - Difficulty Levels`
10. `09 - Skill Levels`
11. `10 - Turnaround Times`
12. `11 - Warranty Options`
13. `12 - Status Values`
14. `13 - Validation Summary`
15. `14 - Revision History`
16. `15 - Import Metadata`

The primary `01 - Master Services` table is
`tblMasterServicesCatalog` and contains exactly the 45 fields in the data
dictionary. `13 - Validation Summary` contains both
`tblMasterServicesValidationSummary` and `tblLaborMatchAudit`. Every other
worksheet contains its single documented Excel Table.

| Worksheet | Excel Table |
|---|---|
| 00 - Instructions | `tblMasterServicesInstructions` |
| 01 - Master Services | `tblMasterServicesCatalog` |
| 02 - Service Categories | `tblServiceCategories` |
| 03 - Repair Types | `tblRepairTypes` |
| 04 - Device Families | `tblDeviceFamilies` |
| 05 - Manufacturers | `tblManufacturers` |
| 06 - Labor Standards | `tblLaborStandardsLookup` |
| 07 - Labor Tiers | `tblLaborTiersLookup` |
| 08 - Difficulty Levels | `tblDifficultyLevels` |
| 09 - Skill Levels | `tblSkillLevels` |
| 10 - Turnaround Times | `tblTurnaroundTimes` |
| 11 - Warranty Options | `tblWarrantyOptions` |
| 12 - Status Values | `tblServiceStatusValues` |
| 13 - Validation Summary | `tblMasterServicesValidationSummary`; `tblLaborMatchAudit` |
| 14 - Revision History | `tblMasterServicesRevisionHistory` |
| 15 - Import Metadata | `tblMasterServicesImportMetadata` |

All Master Services list validations reference these workbook-defined names:

- `DV_YesNo`
- `DV_ServiceStatuses`
- `DV_PricingStatuses`
- `DV_ReviewStatuses`
- `DV_ManufacturerIDs`
- `DV_DeviceFamilyCodes`
- `DV_ServiceCategoryIDs`
- `DV_RepairTypeIDs`
- `DV_LaborStandardIDs`
- `DV_LaborTiers`
- `DV_DifficultyLevels`
- `DV_SkillLevels`
- `DV_TurnaroundTimes`
- `DV_WarrantyOptions`

Direct cross-sheet list-validation formulas are prohibited. Warranty Options
always includes `N/A`.

## Pricing Deferral Rules

`Legacy Retail Price` and `Legacy Cost` are preserved observations only. They are
not approved prices, final costs, pricing inputs, or calculated outputs.

- Price greater than zero: `Legacy Price Review`.
- Price equal to zero: `Pending Pricing Review`.
- Invalid or unavailable observations: `Pending Pricing Review`.
- No final customer price or final cost column is permitted.
- Pricing approval waits for the separately governed Master Pricing Model.

## Conflict Handling

The generator reads reviewed conflict rows from the proposal. Approved decisions
are preserved as reviewer context. An unresolved conflict is not merged or
discarded; its service remains `Draft` with `Pending Review`. Legacy values are
never overwritten. Canonical identity changes occur only in this proposed output.

## Ownership

- Service taxonomy and repair definitions: Repair Engineering.
- Labor standards and mappings: Operations and Labor Planning.
- Pricing status and future pricing model: Pricing Governance.
- Manufacturer and device taxonomy: Product Catalog and Sourcing.
- Workbook schema, validation, and version metadata: Data Engineering.
- Draft preparation owner: Tamara Grandoit.

## Review Workflow

1. Validate the generated workbook independently.
2. Review unresolved SKU conflicts and lookup gaps.
3. Review all `Pending Labor Mapping` services.
4. Review legacy pricing observations without approving final pricing.
5. Confirm service flags, warranty, and turnaround values.
6. Approve or reject proposed service identities.
7. Plan a separate canonical import only after explicit authorization.

## Import Boundary

Generation and validation do not import data. The output workbook is a review
artifact. Any canonical database update requires a separate approved migration,
backup, validation run, ownership sign-off, and rollback plan. PricingEngine and
QuoteEngine are outside this package's scope.
