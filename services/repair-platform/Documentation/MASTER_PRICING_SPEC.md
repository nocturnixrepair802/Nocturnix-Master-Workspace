# Master Pricing Catalog V1 Specification

## Purpose

Master Pricing Catalog V1 is a standalone review framework linking each approved
Master Service to provisional pricing observations, labor references, cost
research, margin research, and regional-market research. It does not calculate,
approve, publish, quote, or import a final customer price.

Planned local output:

`D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Pricing_Catalog_v1.xlsx`

Neither the generator nor validator writes to an input workbook or to
`Data/Nocturnix_Master_Database.xlsm`.

## Scope and Source Precedence

The generated population is exactly one proposed pricing record for each of the
314 rows in `Nocturnix_Master_Services_Catalog_v1.xlsx`, worksheet
`01 - Master Services`, in source order.

Read-only source precedence is:

1. Master Services owns Service ID, service identity, reviewed relationships,
   legacy monetary observations, source pricing status, and provenance.
2. `Nocturnix_Standard_Labor_Catalog_v1.xlsx`, worksheet
   `01 - Labor Standards`, owns Labor Standard IDs and labor attributes.
3. `Nocturnix_Master_Database.xlsm` supplies the authoritative pricing-ID
   namespace from `50 Pricing` and is never written.
4. The deduplication proposal identifies excluded legacy source rows that must
   not re-enter the pricing population.
5. Master Pricing controlled lists own the new pricing-review lifecycle.

All four inputs are protected by SHA-256 checks before and after generation.
They must exist, be nonempty ZIP-based Excel files, and open read-only. The
canonical `.xlsm` is opened with `keep_vba=True`.

## Approved Schema

The proposed 46-field schema used one `Pricing Status` field for two different
meanings: the preserved Master Services pricing status and the new Master
Pricing lifecycle. Those values can differ. V1 therefore adds
`Legacy Pricing Status` immediately before `Pricing Status`. The primary schema
contains 47 fields. ADR-007 accepts this schema and requires the two status
fields to remain separate.

## Identity Rules

ADR-007 establishes Pricing Record IDs in `PRC000001` format with regex
`^PRC\d{6}$`.

At runtime the generator reads `50 Pricing` and:

- accepts sequence values only when they match the regex;
- reports malformed nonblank values but excludes them from sequence math;
- rejects duplicate valid existing IDs;
- allocates a continuous sequence after the highest valid ID in Master Services
  source order; and
- never reuses or renumbers an existing ID.

Read-only inspection on 2026-07-22 found no `Pricing Record ID` header and no
`PRC######` values. The sheet contains legacy pricing examples and
`RULE0000001` through `RULE0000010`, which are not Pricing Record IDs.
ADR-007 approves this as an empty namespace whose first allocation is
`PRC000001`. The current 314-record draft is therefore expected to use
`PRC000001` through `PRC000314`. If valid canonical PRC IDs later exist,
allocation continues dynamically after the highest valid ID.

Service ID remains the relationship key and must match Master Services exactly.
No Service ID is generated or changed.

Pricing Record ID allocation creates draft review identities only. It does not
approve pricing, populate the canonical workbook, or authorize import.

## Workbook Contract

The workbook contains these 13 sheets in this exact order:

1. `00 - Instructions`
2. `01 - Pricing Records`
3. `02 - Pricing Statuses`
4. `03 - Cost Components`
5. `04 - Labor References`
6. `05 - Service References`
7. `06 - Margin Targets`
8. `07 - Regional Markets`
9. `08 - Pricing Methods`
10. `09 - Review Queue`
11. `10 - Validation Summary`
12. `11 - Revision History`
13. `12 - Import Metadata`

| Worksheet | Excel Table |
|---|---|
| 00 - Instructions | `tblMasterPricingInstructions` |
| 01 - Pricing Records | `tblMasterPricingCatalog` |
| 02 - Pricing Statuses | `tblPricingStatuses` |
| 03 - Cost Components | `tblCostComponents` |
| 04 - Labor References | `tblPricingLaborReferences` |
| 05 - Service References | `tblPricingServiceReferences` |
| 06 - Margin Targets | `tblMarginTargets` |
| 07 - Regional Markets | `tblRegionalMarkets` |
| 08 - Pricing Methods | `tblPricingMethods` |
| 09 - Review Queue | `tblPricingReviewQueue` |
| 10 - Validation Summary | `tblMasterPricingValidation` |
| 11 - Revision History | `tblMasterPricingRevisionHistory` |
| 12 - Import Metadata | `tblMasterPricingImportMetadata` |

Every populated range is an Excel Table with a unique name, filters, a frozen
header row, and no merged cells in the table.

## Service and Labor Relationships

- Every Service ID occurs exactly once and resolves to Master Services.
- Manufacturer and device-family ID/name pairs equal the Service reference.
- Legacy Service SKU, service name, monetary observations, legacy pricing
  status, and provenance are copied without reinterpretation.
- Every populated Labor Standard ID exists in the protected labor catalog.
- Standard Labor Minutes and Labor Rate Tier equal the referenced labor row.
- Missing labor mapping is preserved and routed to review.
- Labor Rate and Labor Cost remain blank; a labor standard is not a rate.

Rejected or archived service records and all source rows listed in
`02 - Duplicate Exclusions` are prohibited. The expected reviewed Master
Services input contains 314 eligible Repair services.

## Pricing Lifecycle

Allowed Pricing Status values are:

- Pending Pricing Review
- Legacy Price Review
- Cost Research Required
- Labor Mapping Required
- Market Research Required
- Ready for Pricing Calculation
- Ready for Approval
- Approved
- Rejected
- Archived

Initial generation applies this precedence:

1. Blank Labor Standard ID: `Labor Mapping Required`.
2. Any unresolved required cost input: `Cost Research Required`.
3. Unresolved regional market: `Market Research Required`.
4. Otherwise: `Ready for Pricing Calculation`.

V1 deliberately leaves required internal cost inputs unresolved, so a mapped
labor record is initially `Cost Research Required`. No generated row is
`Ready for Approval` or `Approved`.

Pricing Method is controlled and defaults to `Not Yet Determined`. A legacy
price never determines the pricing method.

## Monetary, Cost, and Calculation Boundaries

Python monetary validation uses `Decimal` semantics. Blank and zero differ:
zero is an observed value; blank means unresolved or unavailable. A zero legacy
cost is not a verified cost, a free service, or a data-quality failure.

Legacy Retail Price and Legacy Cost are copied as historical/provisional
observations. V1 does not populate Part Cost, Shipping Cost, Consumables Cost,
Testing Cost, Labor Rate, Labor Cost, Overhead Allocation, Processing Fees,
Warranty Allowance, Risk Allowance, Total Internal Cost, Target Margin Percent,
Market Adjustment, Recommended Price, Minimum Approved Price, Maximum Approved
Price, or Final Customer Price.

Total Internal Cost stays blank while any required component is unresolved.
Recommended Price and Final Customer Price are always blank in V1. No formula
may calculate them. Negative monetary values are invalid.

Currency remains blank because the reviewed sources do not confirm a row-level
currency. `USD` is included only as a candidate controlled value and is not
defaulted.

## Cost and Market Governance

Cost Components lists the required research areas without amounts: part,
shipping, consumables, testing, labor rate and labor cost, overhead, processing
fees, warranty, and risk. Values require evidence and owner approval.

Margin Targets and Regional Markets contain unresolved placeholders. The
generator does not invent a margin or region. Pricing Governance owns margin
policy; market research owns regional evidence.

## Defined Names

All cross-sheet list validation uses workbook-scoped defined names:

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

Direct cross-sheet list formulas and hard-coded comma-separated governed lists
are prohibited. The reopened generator validation and independent validator
verify each name, target range, and validation formula.

## Review Queue and Workflow

The queue contains:

- Pricing Record ID
- Service ID
- Service Name
- Pricing Status
- Missing Inputs
- Required Action
- Review Priority
- Review Status
- Reviewer Notes

It routes Labor Mapping, Part Cost Research, Shipping Cost Research,
Consumables Review, Testing Cost Review, Labor Rate Review, Overhead Review,
Fee Review, Warranty/Risk Review, Margin Review, Regional Market Review, and
Legacy Price Review. It never invents a resolution.

Review order:

1. Resolve labor mapping.
2. Research required cost components.
3. Review provisional legacy prices.
4. Approve margin policy and regional-market evidence.
5. Only in a later approved model, calculate candidate prices.
6. Separately review and approve pricing before publication or import.

## Ownership and Approval Boundary

- Pricing lifecycle, margin, and approval: Pricing Governance.
- Labor standards and mappings: Operations and Labor Planning.
- Services: Repair Engineering.
- Manufacturer and device relationships: Product Catalog and Sourcing.
- Cost evidence: Procurement and Finance.
- Regional evidence: Market Research and Pricing Governance.
- Workbook construction and validation: Data Engineering.

A passing workbook validates structure and provenance only. It does not approve
pricing, authorize publication, create a quote source, or authorize canonical
import. Canonical import requires a separate approved migration with backup,
sign-off, and rollback controls.

## Known Limitations and Unresolved Decisions

- ADR-007 resolves Pricing Record ID identity and approves the 47-column schema.
- Currency is not confirmed by the source artifacts.
- Required cost components, labor rates, margin targets, and regions are
  unresolved.
- Pricing formulas, rounding policy per currency, approval roles, effective-date
  rules, and publication integration are outside V1.
- Canonical `50 Pricing` contains legacy examples whose units and governance are
  unresolved; they are not imported into this artifact.
- All initial records remain draft review records, and no Final Customer Price
  is approved.
