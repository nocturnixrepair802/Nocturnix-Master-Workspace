# Master Devices Catalog V1 Data Dictionary

ADR-009 is the authority for Device identity, identifier allocation, and the
accepted schema.

The primary table is `tblMasterDevicesCatalog` on `01 - Master Devices`.
It contains exactly 48 columns in this order.

| # | Field | Type | Required | Source / transformation, meaning, lookup, and validation |
|---:|---|---|---|---|
| 1 | Device ID | Text | Yes | `DEV` plus six digits; runtime canonical continuation. |
| 2 | Legacy Device SKU | Text | Yes | Preserved alias/reference; not a primary key. |
| 3 | Active | Controlled text | Yes | Generated `Yes`. |
| 4 | Status | Controlled text | Yes | Generated `Draft`. |
| 5 | Manufacturer ID | Text | Conditional | Exact canonical-name match only. |
| 6 | Manufacturer Name | Text | Yes | Original legacy observation. |
| 7 | Device Family Code | Text | Conditional | Exact canonical family mapping only. |
| 8 | Device Family Name | Text | Conditional | Must agree with family code. |
| 9 | Product Line | Text | No | Legacy Group observation. |
| 10 | Device Series | Text | No | Blank unless supported by explicit evidence. |
| 11 | Device Name | Text | Yes | Legacy Name. |
| 12 | Device Display Name | Text | Yes | Legacy Name. |
| 13 | Device Description | Text | No | Legacy Note. |
| 14 | Model Number | Text | No | Never inferred in V1. |
| 15 | Variant | Text | No | Never inferred in V1. |
| 16 | Generation | Text | No | Never inferred in V1. |
| 17 | Release Year | Integer | No | Four-digit year when approved; blank in V1. |
| 18 | Form Factor | Controlled text | No | Blank pending taxonomy review. |
| 19 | Operating System Family | Controlled text | No | Blank pending review. |
| 20 | Network Type | Controlled text | No | Blank pending review. |
| 21 | Storage Capacity | Text | No | Blank; no parsing from names. |
| 22 | Memory Capacity | Text | No | Blank; no parsing from names. |
| 23 | Color | Text | No | Blank; no parsing from names. |
| 24 | Region | Text | No | Blank. |
| 25 | Carrier | Text | No | Blank. |
| 26 | Wi-Fi Only | Yes/No | Yes | Generated `No`; not inferred. |
| 27 | Cellular Capable | Yes/No | Yes | Generated `No`; not inferred. |
| 28 | Repair Supported | Yes/No | Yes | Generated `No`; approval deferred. |
| 29 | Parts Supported | Yes/No | Yes | Generated `No`; approval deferred. |
| 30 | Mail-In Eligible | Yes/No | Yes | Generated `No`; approval deferred. |
| 31 | Mobile Service Eligible | Yes/No | Yes | Generated `No`; approval deferred. |
| 32 | Compatibility Status | Controlled text | Yes | Generated `Pending Compatibility Review`. |
| 33 | Service Mapping Status | Controlled text | Yes | Generated `Pending Service Mapping`. |
| 34 | Parts Mapping Status | Controlled text | Yes | Generated `Pending Parts Mapping`. |
| 35 | Review Status | Controlled text | Yes | Most restrictive unresolved identity status. |
| 36 | Legacy Retail Price | Decimal | No | Provisional source observation; no calculation. |
| 37 | Legacy Cost | Decimal | No | Provisional source observation; no calculation. |
| 38 | Currency | Controlled text | No | Blank; never defaulted. |
| 39 | Source Record Number | Integer | Yes | Proposal source row; unique in this catalog. |
| 40 | Source Workbook | Text | Yes | Preserved provenance. |
| 41 | Source Worksheet | Text | Yes | Preserved provenance. |
| 42 | Import Batch ID | Text | Yes | `MASTER-DEVICES-V1-REVIEW`. |
| 43 | Reviewer | Text | No | Blank until reviewed. |
| 44 | Reviewer Notes | Text | No | Original Legacy Note observation. |
| 45 | Effective Date | Date | No | Blank until approved. |
| 46 | Last Reviewed | Date/time | No | Blank until reviewed. |
| 47 | Created At | Date/time | No | Preserved source value. |
| 48 | Updated At | Date/time | No | Preserved source value. |

For controlled text fields, valid values are the corresponding defined-name
lookup documented in the specification. For free-text fields, surrounding
whitespace is normalized only for comparison; substantive source text is
preserved. For monetary fields, blank means unobserved, numeric zero remains a
real zero observation, negative and nonnumeric values fail, and Currency
remains blank until policy is established.

## Controlled Values

- Device Status: Draft, Active, Planned, Future, Discontinued, Archived,
  Rejected.
- Review Status: Pending Review, Pending Manufacturer Review, Pending Family
  Review, Pending Identity Review, Pending Relationship Review, Ready for
  Approval, Approved, Rejected, Archived.
- Compatibility Status: Pending Compatibility Review, Family-Level Only,
  Model-Level Proposed, Variant-Level Proposed, Not Applicable, Approved,
  Rejected.
- Service Mapping Status: Pending Service Mapping, Family Services Available,
  Model Services Proposed, Complete, Not Applicable, Approved, Rejected.
- Parts Mapping Status: Pending Parts Mapping, Family Parts Available, Model
  Parts Proposed, Complete, Not Applicable, Approved, Rejected.
- Boolean fields: Yes, No.
- Currency lookup: USD. Generated Currency remains blank because V1 does not
  infer a currency.

Manufacturer ID, Device Family Code, Product Line, Device Series, Form Factor,
Operating System Family, and Network Type use their documented lookup tables
and workbook-defined names. A blank conditional relationship must route to the
appropriate pending review status.

## Supporting Tables

| Worksheet | Table | Purpose |
|---|---|---|
| 00 - Instructions | `tblMasterDevicesInstructions` | Review and governance instructions. |
| 02 - Manufacturers | `tblDeviceManufacturers` | Canonical manufacturer snapshot. |
| 03 - Device Families | `tblDeviceFamilies` | Canonical family snapshot. |
| 04 - Product Lines | `tblProductLines` | Source-observed product-line candidates. |
| 05 - Device Series | `tblDeviceSeries` | Controlled series review list. |
| 06 - Form Factors | `tblFormFactors` | Controlled form-factor list. |
| 07 - Operating Systems | `tblOperatingSystems` | Controlled OS-family list. |
| 08 - Network Types | `tblNetworkTypes` | Controlled network-type list. |
| 09 - Device Statuses | `tblDeviceStatuses` | Status, Yes/No, and currency controls. |
| 10 - Identity Review | `tblDeviceIdentityReview` | All generated identities requiring review. |
| 11 - Relationship Review | `tblDeviceRelationshipReview` | Compatibility/service/parts review queue. |
| 12 - Validation Summary | `tblMasterDevicesValidation` | Generator validation outcomes. |
| 13 - Revision History | `tblMasterDevicesRevisionHistory` | Artifact revision history. |
| 14 - Import Metadata | `tblMasterDevicesImportMetadata` | Provenance, hashes, counts, and ID evidence. |

## Identity Review Columns

`Device ID`, `Legacy Device SKU`, `Manufacturer Name`, `Device Family Name`,
`Product Line`, `Device Series`, `Device Name`, `Model Number`, `Variant`,
`Missing Identity Inputs`, `Identity Concern`, `Required Action`,
`Review Status`, `Reviewer Notes`.

## Relationship Review Columns

`Device ID`, `Device Name`, `Manufacturer ID`, `Device Family Code`,
`Compatibility Status`, `Service Mapping Status`, `Parts Mapping Status`,
`Missing Relationships`, `Required Action`, `Review Status`, `Reviewer Notes`.

## Prohibited Fields

The schema intentionally excludes customer serial number, IMEI, stock, bin,
location, inventory quantity, final cost, markup, margin, and final customer
price.
