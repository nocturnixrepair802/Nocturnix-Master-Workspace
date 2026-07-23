# Master Devices Catalog V1 Specification

## Purpose and Scope

Master Devices Catalog V1 is a standalone proposed canonical review artifact.
It creates one draft device-identity row for every retained legacy Device
record.

Planned output:

`D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Devices_Catalog_v1.xlsx`

The package does not update the canonical database, customer devices,
inventory, Master Services, Master Parts, Master Pricing, compatibility, or
application runtime code.

## Authority, Source Precedence, and Protected Inputs

ADR-009 establishes the Device ID namespace and accepts the 48-column schema.
All inputs are opened read-only and protected by SHA-256 hashes before and
after generation:

1. Legacy deduplication proposal.
2. Master Services Catalog V1.
3. Master Parts Catalog V1.
4. Master Pricing Catalog V1.
5. `Data/Nocturnix_Master_Database.xlsm`.

The canonical workbook is opened with `read_only=True`, `data_only=True`, and
`keep_vba=True`. It is never saved.

Source precedence is:

1. Proposal `01 - Retained` owns the retained Device population, legacy
   observations, and provenance.
2. Canonical `32 Devices` owns existing Device ID namespace evidence.
3. Canonical `30 Manufacturers` and `31 Device Families` own approved lookup
   identifiers and names.
4. Master Services, Master Parts, Master Pricing, and canonical relationship
   areas are protected context only; they do not supply inferred V1 identity,
   relationship, or pricing values.

## Source Population

Filter proposal `01 - Retained` to `Record Category = Device`. Runtime checks
must reconcile the current expected count of 46, preserve every source row once,
and retain ascending Source Record Number order. Duplicate-exclusion rows are
not reintroduced.

## Device Identity Boundary

Master Devices owns reusable catalog identity and taxonomy. It does not own:

- customer serial numbers or IMEIs;
- stock, bin, location, or inventory quantity;
- customer-device condition;
- service or parts compatibility approval;
- final or published pricing.

Legacy condition is therefore not part of the schema. Legacy retail price and
cost are retained only as provisional observations.

## Device ID Allocation

At runtime, read the exact `Device ID` column from canonical worksheet
`32 Devices`.

- Valid IDs match `^DEV\d{6}$`.
- Duplicate valid IDs fail.
- Malformed populated IDs are reported and excluded from sequence arithmetic.
- When valid IDs exist, allocation begins at highest valid ID plus one.
- An empty valid namespace begins at ADR-009's approved `DEV000001`.
- Generated IDs form one continuous sequence in source-row order.
- Generated IDs may not collide with canonical IDs.

Current evidence establishes `DEV000842` as the highest valid canonical ID, so
the current 46-row expected range is `DEV000843` through `DEV000888`.

## Conservative Source Mapping

- Legacy SKU -> Legacy Device SKU.
- Legacy Name -> Device Name and Device Display Name.
- Legacy Group -> Product Line observation.
- Explicit `Device - Phone` or `Device - Tablet` type -> exact canonical Device
  Family candidate.
- Legacy Manufacturer -> Manufacturer Name observation; Manufacturer ID is
  populated only by exact canonical-name match.
- Legacy Note -> Device Description and Reviewer Notes.
- Legacy Retail Price and Legacy Cost -> exact provisional observations.
- Source timestamps and provenance -> corresponding audit fields.

The generator does not infer Model Number, Variant, Generation, Release Year,
Form Factor, Operating System Family, Network Type, Storage Capacity, Memory
Capacity, Color, Region, Carrier, compatibility, repair support, parts support,
or service/parts mappings.

## Defaults and Review Routing

Generated rows use:

- Active: Yes.
- Status: Draft.
- Wi-Fi Only: No.
- Cellular Capable: No.
- Repair Supported: No.
- Parts Supported: No.
- Mail-In Eligible: No.
- Mobile Service Eligible: No.
- Compatibility Status: Pending Compatibility Review.
- Service Mapping Status: Pending Service Mapping.
- Parts Mapping Status: Pending Parts Mapping.

Review Status is:

1. `Pending Manufacturer Review` when Manufacturer ID is blank.
2. `Pending Family Review` when Device Family Code is blank.
3. Otherwise `Pending Identity Review`.

No generated row is Approved or Ready for Approval.

## Monetary Boundary

Legacy Retail Price and Legacy Cost use decimal semantics. Numeric zero remains
zero; blank remains blank; negative values fail. Currency is not defaulted.
No price, cost, markup, margin, or customer price is calculated or published.

## Workbook Contract

The exact 15-sheet order is:

1. `00 - Instructions`
2. `01 - Master Devices`
3. `02 - Manufacturers`
4. `03 - Device Families`
5. `04 - Product Lines`
6. `05 - Device Series`
7. `06 - Form Factors`
8. `07 - Operating Systems`
9. `08 - Network Types`
10. `09 - Device Statuses`
11. `10 - Identity Review`
12. `11 - Relationship Review`
13. `12 - Validation Summary`
14. `13 - Revision History`
15. `14 - Import Metadata`

Every worksheet contains one documented Excel Table with a unique name, filter,
and frozen header row.

## Defined Names

All list validations use workbook-scoped defined names:

- `DV_YesNo`
- `DV_DeviceStatuses`
- `DV_ReviewStatuses`
- `DV_CompatibilityStatuses`
- `DV_ServiceMappingStatuses`
- `DV_PartsMappingStatuses`
- `DV_ManufacturerIDs`
- `DV_DeviceFamilyCodes`
- `DV_ProductLines`
- `DV_DeviceSeries`
- `DV_FormFactors`
- `DV_OperatingSystemFamilies`
- `DV_NetworkTypes`
- `DV_Currencies`

Direct cross-sheet list formulas are prohibited.

## Transactional Output

The generator saves to a sibling `.tmp.xlsx` path, validates the reopened
temporary workbook, verifies protected hashes, and then atomically replaces the
final output. Failures remove the temporary file and do not replace the final
artifact. All workbook-bound temporal values pass through the generic
Excel-safe conversion policy.

## Limitations and Governance

A passing workbook remains a review artifact. Manufacturer aliases, product
line/series taxonomy, precise model identities, hardware attributes, service
relationships, parts relationships, and compatibility require human review.
Canonical import is outside V1.

## Review Workflow and Ownership

1. Catalog Governance resolves manufacturer aliases and duplicate identity
   concerns.
2. Product Catalog confirms family, product line, series, model, model number,
   variant, and generation.
3. Repair Engineering reviews compatibility and Master Services relationships.
4. Parts Governance reviews Master Parts relationships.
5. Finance may review legacy monetary observations, but V1 does not approve or
   publish pricing.
6. Data Engineering governs workbook validation and any separately authorized
   canonical-import process.
