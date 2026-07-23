# Master Parts Catalog V1 Specification

## Purpose and Scope

Master Parts Catalog V1 is a standalone proposed canonical review artifact. It
creates one draft catalog row for every retained legacy Part record and
separates part identity from inventory, sourcing approval, compatibility
approval, and final pricing.

Planned output:

`D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Parts_Catalog_v1.xlsx`

The package does not update the canonical database, inventory, Master Services,
Master Pricing, supplier pricing, or application engines.

## Authority and Source Precedence

ADR-008 establishes Part ID identity and accepts the 50-column schema.

Read-only source precedence:

1. Deduplication proposal `01 - Retained` owns the retained Part population,
   legacy observations, and provenance.
2. Canonical `30 Manufacturers`, `31 Device Families`, `32 Devices`, and
   `43 Suppliers` provide lookup evidence.
3. Canonical `39.4 Repair Parts` and `41 Parts` provide the runtime Part ID
   namespace evidence.
4. Master Services supplies warranty lookup values and protected relationship
   context.
5. Master Pricing is protected context only and supplies no part prices.

The proposal, Master Services, Master Pricing, and canonical database are
protected by SHA-256 checks before and after generation. All are opened
read-only; the canonical `.xlsm` uses `keep_vba=True`.

## Source Population

Filter proposal `01 - Retained` to `Record Category = Part`. Runtime validation
must reconcile the current expected count of 48 and preserve ascending Source
Row Number order. No retained Part is discarded, no non-Part is imported, and
no duplicate-exclusion row is reintroduced.

## Catalog Versus Inventory

Part identity uses stable descriptive evidence: name, type, manufacturer,
device applicability, model number, capacity, color, quality, and OEM status.
Legacy stock, serial number, condition, bin, tax status, and location are not
identity keys. Condition is preserved as a review observation only.

`Inventory Tracked = Yes` is a conservative proposed review default for physical
parts. It neither creates inventory nor establishes stock-on-hand.

## Part Identity

Part IDs match `^PRT\d{6}$`. At runtime the scripts inspect exact `Part ID`
columns in `39.4 Repair Parts` and `41 Parts`.

- Valid existing IDs cause dynamic continuation after the highest.
- Duplicate valid existing IDs fail validation.
- Malformed populated IDs are reported and excluded from sequence math.
- No valid existing IDs invokes ADR-008's empty namespace at `PRT000001`.
- IDs are assigned in ascending Source Record Number order.
- Legacy Part SKU remains an alias/reference.
- Supplier differences alone neither merge nor split identity.

Current evidence shows an empty `39.4 Repair Parts!Part ID` column and no Part ID
column in `41 Parts`, so the expected 48-row range is `PRT000001` through
`PRT000048`.

## Source Mapping

- Legacy SKU -> Legacy Part SKU.
- Legacy Name -> Part Name and Part Display Name.
- Legacy Group -> proposed Part Category and deterministic proposed category ID.
- Legacy Type -> proposed Part Type and deterministic proposed type ID.
- Legacy Manufacturer -> Manufacturer Name observation; exact canonical name
  match may populate Manufacturer ID.
- Legacy Supplier -> Supplier Name observation. Supplier ID remains blank when
  the canonical supplier sheet has no approved ID.
- Legacy Retail Price and Legacy Cost -> exact provisional observations.
- Legacy Condition -> Condition observation.
- Legacy Note -> Reviewer Notes.
- Source Created/Updated At -> Created At/Updated At.
- Source Row Number -> Source Record Number.

Device ID, precise compatibility, part quality, OEM status, color, capacity,
model number, supplier part number, preferred supplier, currency, and warranty
are not inferred.

## Manufacturer and Device Mapping

Manufacturer IDs populate only for unambiguous case-insensitive name matches to
canonical Manufacturers. Missing or unmatched values remain observations and
route to `Pending Manufacturer Review`.

Device Family may be conservatively mapped from an explicit legacy type such as
`Part - Phone`; Device ID remains blank unless exact source evidence exists.
Missing device applicability routes to device or compatibility review.

## Compatibility Boundary

Compatibility is reviewed in `10 - Compatibility Review`. A family-only mapping
may use `Device Family Only`; otherwise generated rows use
`Pending Compatibility Review`. No canonical Compatibility Matrix write occurs.

## Supplier Boundary

Observed supplier names are preserved but are not preferred suppliers. Supplier
IDs and supplier part numbers remain blank without approved evidence.
Multi-supplier sourcing belongs in a future relationship structure.

## Cost and Pricing Boundary

Legacy Cost and Legacy Retail Price are provisional source observations.
Numeric zero remains zero but is not an approved cost or price. Blank remains
unresolved. Negative observations fail validation. Currency is not defaulted.

V1 does not calculate supplier cost, landed cost, markup, margin, selling price,
or Final Customer Price.

## Status Lifecycle

Generated values are conservative review defaults:

- Active: Yes.
- Status: Draft.
- Preferred Supplier: No.
- Inventory Tracked: Yes.
- Serialized: No.
- Warranty Eligible: No.
- Compatibility Status: Pending Compatibility Review unless family evidence is
  sufficient.
- Sourcing Status: Supplier Observed or Supplier Unknown.
- Cost Status: Legacy Cost Only when populated, otherwise Pending Cost Review.
- Pricing Status: Legacy Price Review for positive numeric observations,
  otherwise Pending Pricing Review.
- Review Status: the most restrictive unresolved relationship status.

No generated status is Approved or Ready for Approval.

## Workbook Contract

The exact 15-sheet order is:

1. `00 - Instructions`
2. `01 - Master Parts`
3. `02 - Part Categories`
4. `03 - Part Types`
5. `04 - Manufacturers`
6. `05 - Device Families`
7. `06 - Device References`
8. `07 - Suppliers`
9. `08 - Part Qualities`
10. `09 - Conditions`
11. `10 - Compatibility Review`
12. `11 - Sourcing Review`
13. `12 - Validation Summary`
14. `13 - Revision History`
15. `14 - Import Metadata`

Every populated worksheet has one documented Excel Table, unique table name,
filter, frozen header row, and no merged table cells.

## Defined Names

All cross-sheet list validations use workbook-scoped defined names:

- `DV_PartStatuses`
- `DV_ReviewStatuses`
- `DV_CompatibilityStatuses`
- `DV_SourcingStatuses`
- `DV_CostStatuses`
- `DV_PricingStatuses`
- `DV_PartCategoryIDs`
- `DV_PartTypeIDs`
- `DV_ManufacturerIDs`
- `DV_DeviceFamilyCodes`
- `DV_DeviceIDs`
- `DV_SupplierIDs`
- `DV_PartQualities`
- `DV_Conditions`
- `DV_WarrantyOptions`
- `DV_YesNo`

Direct cross-sheet list formulas are prohibited.

## Review Workflow and Ownership

1. Review part identity and category/type proposals.
2. Resolve manufacturer mappings.
3. Resolve device-family/device compatibility.
4. Review sourcing observations and supplier relationships.
5. Review provisional costs and legacy prices.
6. Approve catalog identities only through a separate workflow.

Part taxonomy: Product Catalog. Manufacturer/supplier evidence: Sourcing and
Procurement. Compatibility: Repair Engineering. Cost evidence: Procurement and
Finance. Workbook governance: Data Engineering.

## Import Prohibition and Limitations

A passing workbook is only structurally valid and traceable. It does not approve
canonical import, inventory creation, purchasing, supplier pricing, cost,
compatibility, or selling price.

Unresolved areas include quality/OEM taxonomies, supplier IDs and relationship
schema, part-to-device compatibility, warranty policy, currency, landed-cost
policy, inventory integration, and final pricing.
