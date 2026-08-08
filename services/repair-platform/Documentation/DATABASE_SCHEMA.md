# Database Schema

Last updated: 2026-07-22
Status: Documentation baseline; no workbook migration has been performed
System of record: `Data/Nocturnix_Master_Database.xlsm`

## Purpose and evidence rules

This document inventories every table currently configured in
`Source/config/database.py::TABLES` and observed through `TableLoader`.

- **Current workbook schema** records columns and Python value types actually loaded.
- **Temporary adapter contract** describes a non-destructive translation that may be
  used before a workbook migration. It is not implemented unless explicitly stated.
- **Canonical target schema** is approved design direction, not current functionality.
- Primary keys, foreign keys, required fields, and unique constraints are not enforced
  by Excel or `TableLoader`. They are labeled **observed**, **inferred**, or
  **proposed** accordingly.
- `empty` means all currently loaded values are null; no data type can be observed.
- Row counts include blank Excel table rows returned by the loader.

## Configured table inventory

| Database key | Excel table | Rows observed |
|---|---|---:|
| `customers` | `tblCustomers` | 10 |
| `customer_devices` | `tblCustomerDevices` | 1 blank row |
| `repair_tickets` | `tblRepairTickets` | 1 blank row |
| `diagnostics` | `tblDiagnostics` | 1 blank row |
| `manufacturer_catalog` | `tblManufacturerCatalog` | 35 |
| `device_catalog` | `tblDeviceCatalog` | 7 |
| `master_devices` | `tblMasterDevices` | 842 |
| `service_types` | `tblServiceTypes` | 29, including one mostly blank row |
| `master_services` | `tblMasterServices` | 75 |
| `compatibility` | `tblCompatibilityID` | 82 |
| `guide_categories` | `tblGuideCategories` | 16, including a header-like data row |
| `guide_sources` | `tblGuideSources` | 8 |
| `repair_guides` | `tblRepairGuides` | 2,380, including 456 largely blank rows |
| `technical_library` | `tblTechnicalLibrary` | 2 blank rows |
| `parts_catalog` | `tblPartsCatalog` | 1 blank row |
| `supplier_catalog` | `tblSupplierCatalog` | 9 |
| `labor_rates` | `tblLaborRates` | 10 |
| `parts_pricing` | `tblParts` | 3, including two blank rows |
| `retail_pricing` | `tblRetailPricing` | 6, mostly blank/default rows |
| `profit_margin` | `tblProfitMargin` | 2 |

## Current schema details and target contracts

### `customers` / `tblCustomers`

**Current workbook schema**

- Columns and observed types: `Customer ID` (str), `Customer Type` (str),
  `First Name` (str), `Last Name` (str/empty), `Business Name` (str/empty), `Email`
  (str), `Mobile Phone` (str), `Home Phone` (empty), `Work Phone` (empty),
  `Preferred Contact` (empty), `Billing Address` (empty), `Shipping Address` (empty),
  `Tax Exempt` (bool/empty), `Active` (bool/empty), `Date Created` (empty),
  `Last Modified` (empty), `Notes` (empty).
- Primary key: `Customer ID` is an observed unique candidate (10/10 non-null and
  unique); not enforced.
- Foreign keys: none evidenced.
- Required fields: observed non-null fields are `Customer ID`, `Customer Type`,
  `First Name`, `Email`, and `Mobile Phone`. Business requirements are not enforced.
- Unique constraints: `Customer ID` is observed unique. Email and mobile phone are
  also unique in the sample but are not approved constraints.
- Known problems: nullable `Last Name`, `Tax Exempt`, and `Active`; audit fields are
  unpopulated; address fields are unstructured and empty.

**Temporary adapter contract**

Expose existing names unchanged; normalize nullable Boolean fields at the service
boundary only after an approved default is defined.

**Canonical target schema**

Retain current columns initially. Proposed required fields: `Customer ID`, `Customer
Type`, `First Name` or `Business Name` according to customer type, at least one contact
method, `Tax Exempt`, `Active`, `Date Created`, and `Last Modified`. Proposed unique
constraint: `Customer ID` only until email/phone duplicate policy is approved.

**Migration notes**

Backfill Boolean and audit values before enforcing requirements. Address normalization
is a separate migration and is not approved by this document.

### `customer_devices` / `tblCustomerDevices`

**Current workbook schema**

- Columns and observed types: `Device ID`, `Customer ID`, `Manufacturer`, `Device
  Family`, `Device Model`, `Serial Number`, `IMEI / Service Tag`, `Color`, `Storage`,
  `Carrier`, `Purchase Date`, `Warranty Expiration`, and `Notes` are empty; `Active`
  is bool (`False`) in the blank row.
- Primary key: `Device ID` is inferred by name; no populated evidence.
- Foreign keys: `Customer ID` -> `customers.Customer ID` is inferred. The device fields
  are descriptive and do not currently reference `master_devices.Device ID` clearly.
- Required fields and unique constraints: undefined from current data.
- Known problems: only a blank placeholder row exists; `Device ID` conflicts
  semantically with the master-device identifier; manufacturer/family/model are
  denormalized descriptions.

**Temporary adapter contract**

Treat blank rows as no records. Do not infer a valid customer-device relationship
from the placeholder.

**Canonical target schema**

Proposed columns: `Customer Device ID` (PK), `Customer ID` (FK), `Master Device ID`
(FK), `Serial Number`, `IMEI / Service Tag`, `Color`, `Storage`, `Carrier`, `Purchase
Date`, `Warranty Expiration`, `Active`, `Notes`.

**Migration notes**

Resolve identifier meaning before renaming. Populate relationships through validated
customer and master-device IDs; do not migrate the blank row.

### `repair_tickets` / `tblRepairTickets`

**Current workbook schema**

- Columns and observed types: all values are empty for `Ticket ID`, `Customer ID`,
  `Device ID`, `Repair Status`, `Intake Date`, `Technician`, `Problem Description`,
  `Diagnosis`, `Estimated Cost`, `Final Cost`, `Date Completed`, `Date Picked Up`,
  `Warranty`, and `Notes`.
- Primary key: `Ticket ID` is inferred; no populated evidence.
- Foreign keys: `Customer ID` -> customers and `Device ID` -> customer devices are
  inferred. Technician has no configured reference table.
- Required fields, unique constraints, and types: undefined from current data.
- Known problems: blank placeholder row; monetary and date types cannot be observed;
  status vocabulary is not enforced.

**Temporary adapter contract**

Treat the blank row as no ticket. Continue exposing current field names to existing
repositories and GUI code.

**Canonical target schema**

Retain current fields with explicit types. Proposed required fields: `Ticket ID`,
`Customer ID`, `Customer Device ID`, `Repair Status`, `Intake Date`, and `Problem
Description`. Proposed PK/unique constraint: `Ticket ID`. Use decimal for monetary
fields and a controlled status vocabulary.

**Migration notes**

Coordinate the `Device ID` rename with the customer-device identifier decision.

### `diagnostics` / `tblDiagnostics`

**Current workbook schema**

- Columns and observed types: `CustomerID`, `FirstName`, `LastName`, `Phone`, and
  `Email` are all empty.
- Primary key: none present.
- Foreign keys: `CustomerID` appears intended to reference customers, but naming does
  not match `Customer ID` and there is no evidence.
- Required fields and unique constraints: undefined.
- Known problems: blank placeholder row; no diagnostic identifier, ticket link,
  device link, diagnostic result, timestamps, or normalized names.

**Temporary adapter contract**

No adapter is approved. Treat the table as an unusable placeholder.

**Canonical target schema**

Unresolved. At minimum, a future diagnostic record would require a unique diagnostic
ID and an explicit repair-ticket relationship, but exact fields require business
requirements before approval.

**Migration notes**

Do not invent or migrate records until the diagnostic workflow is defined.

### `manufacturer_catalog` / `tblManufacturerCatalog`

**Current workbook schema**

- Columns and observed types: `Manufacturer ID` (str), `Manufacturer` (str), `Website`
  (str), `Active` (bool), `Notes` (empty).
- Primary key: `Manufacturer ID` is observed unique and non-null.
- Foreign keys: none.
- Required fields: all except `Notes` are populated in current data.
- Unique constraints: `Manufacturer ID`, `Manufacturer`, and `Website` are observed
  unique; only the ID is proposed as an enforced identifier.
- Known problems: no significant observed schema defect.

**Temporary adapter contract**

Identity mapping.

**Canonical target schema**

Retain current columns. Require `Manufacturer ID`, `Manufacturer`, and `Active`;
validate `Website` only when present. Proposed unique constraints: ID and normalized
manufacturer name.

**Migration notes**

Validate all `master_devices.Manufacturer Code` values before enforcing the FK.

### `device_catalog` / `tblDeviceCatalog`

**Current workbook schema**

- Columns and observed types: `Device Family Code` (str), `Device Family` (str),
  `Description` (str), `Active` (bool).
- Primary key: `Device Family Code` is observed unique and non-null.
- Foreign keys: none.
- Required fields: all current fields are populated.
- Unique constraints: code and name are observed unique.
- Known problems: no significant observed schema defect.

**Temporary adapter contract**

Identity mapping.

**Canonical target schema**

Retain all columns. Require code, name, and active status; unique code and normalized
name.

**Migration notes**

Validate all family codes in master devices and compatibility before enforcement.

### `master_devices` / `tblMasterDevices`

**Current workbook schema**

- Columns and observed types: `Device ID` (str), `Manufacturer Code` (str), `Device
  Family Code` (str), `Device Model` (str), `Model Number` (str/empty), `Release Year`
  (float/empty), `End of Support` (empty), `Active` (str/empty), `Notes` (empty).
- Primary key: `Device ID` is observed unique and non-null.
- Foreign keys: `Manufacturer Code` -> `manufacturer_catalog.Manufacturer ID` and
  `Device Family Code` -> `device_catalog.Device Family Code` are inferred and
  consistent by naming.
- Required fields: ID, manufacturer code, family code, and model are populated.
- Unique constraints: `Device ID` and `Device Model` are observed unique; model-number
  uniqueness is not safe because duplicates exist and 282 values are null.
- Known problems: `Release Year` loads as float; `Active` is null for 841 rows and
  contains one string `#N/A`; end-of-support is entirely empty.

**Temporary adapter contract**

Convert integral release years to nullable integers for consumers. Treat invalid or
missing active values as unknown, not automatically true or false.

**Canonical target schema**

Retain columns with `Release Year` as nullable integer, `End of Support` as nullable
date/year according to an approved definition, and `Active` as required Boolean.
Require ID, manufacturer code, family code, model, and active state.

**Migration notes**

Resolve the `#N/A` formula/error and approve an active-state default before backfill.

### `service_types` / `tblServiceTypes`

**Current workbook schema**

- Columns and observed types: `Service Category` (str/empty), `Service Type`
  (str/empty); `Description`, `Default Warranty`, `Default Labor Time`, `Taxable`, and
  `Active` are entirely empty.
- Primary key: none present. `Service Type` is observed unique for 28 populated rows.
- Foreign keys: none evidenced.
- Required fields and constraints: undefined; one row is mostly blank.
- Known problems: no stable identifier; category terminology differs from
  `master_services.Service Category`; all policy/default columns are empty.

**Temporary adapter contract**

Drop fully blank rows in read views. Use populated `Service Type` as a temporary
lookup label only, not a durable key.

**Canonical target schema**

Requires a design decision: either make this a category/type lookup with stable IDs
or retire it in favor of `master_services`. No canonical columns beyond an ID, name,
and active state are approved yet.

**Migration notes**

Reconcile duplicated service taxonomy before adding relationships.

### `master_services` / `tblMasterServices`

**Current workbook schema**

- Columns and observed types: `Service ID` (str), `Service Name` (str), `Service
  Category` (str), `Repair Type` (str), `Requires Part ` (bool), `Requires Labor`
  (bool), `Estimated Labor (hrs)` (empty), `Warranty Eligible` (bool), `Repair
  Difficulty` (empty), `Active` (bool), `Notes` (empty).
- Primary key: `Service ID` is observed unique and non-null.
- Foreign keys: service category/type relationships are not explicit.
- Required fields: all populated nonempty columns are candidates; no enforcement.
- Unique constraints: service ID and service name are observed unique.
- Known problems: trailing space in `Requires Part `; estimated labor is entirely
  empty; taxonomy does not directly align with `service_types` or `labor_rates`.

**Temporary adapter contract**

Alias `Requires Part ` to `Requires Part` in code-facing adapters. Preserve source
column until controlled workbook migration.

**Canonical target schema**

`Service ID`, `Service Name`, `Service Category ID` or an approved normalized category,
`Repair Type`, `Requires Part`, `Requires Labor`, `Estimated Labor Hours`, `Warranty
Eligible`, `Repair Difficulty`, `Active`, `Notes`.

**Migration notes**

Choose the service taxonomy and labor-duration source before renaming columns.

### `compatibility` / `tblCompatibilityID`

**Current workbook schema**

- Columns and observed types: `Compatibility ID` (str), `Device Family` (str),
  `Service Name` (str containing service IDs), `Supported` (bool), `Requires
  Capability` (empty), `Notes` (empty).
- Primary key: `Compatibility ID` is observed unique and non-null.
- Foreign keys: current `Device Family` values appear to reference
  `device_catalog.Device Family Code`; `Service Name` values appear to reference
  `master_services.Service ID`.
- Required fields: ID, family, service value, and supported state are populated.
- Unique constraints: ID is observed unique. The proposed family/service pair must be
  checked for duplicates before enforcement.
- Known problems: `Service Name` is mislabeled; `Device Family` contains codes rather
  than names; current engine expects absent `Service ID`; engine ignores `Supported`.

**Temporary adapter contract**

Expose `Device Family Code` from current `Device Family` and `Service ID` from current
`Service Name`; preserve `Supported`, `Requires Capability`, and `Notes`.

**Canonical target schema**

`Compatibility ID`, `Device Family Code`, `Service ID`, `Supported`, `Requires
Capability`, `Notes`. Proposed unique constraint: `(Device Family Code, Service ID)`.

**Migration notes**

Validate both foreign keys and pair uniqueness before renaming workbook columns.

### `guide_categories` / `tblGuideCategories`

**Current workbook schema**

- Columns and observed types: `Category ID`, `Category Name`, and `Category
  Description` are str; `Display Order`, `Active`, `Created Date`, `Modified Date`, and
  `Notes` are empty.
- Primary key: `Category ID` appears unique, but one data row contains literal
  `Category ID` and is not a valid identifier.
- Foreign keys: none.
- Required fields: category ID/name/description are populated, including the invalid
  header-like row.
- Unique constraints: ID and name are observed unique only because the header-like row
  is counted as data.
- Known problems: duplicated header row stored as data; lifecycle/order fields empty.

**Temporary adapter contract**

Exclude the header-like row where ID equals `Category ID` and name equals `Category
Name`.

**Canonical target schema**

Retain columns with typed `Display Order` integer, `Active` Boolean, created/modified
datetimes, and unique ID/name.

**Migration notes**

Remove the invalid row only through an approved workbook migration with backup.

### `guide_sources` / `tblGuideSources`

**Current workbook schema**

- Columns and observed types: `Source ID`, `Source Name`, and `Source Type` are str;
  `Website`, `License Type`, `Requires Internet`, `Active`, `Created Date`, `Modified
  Date`, and `Notes` are empty.
- Primary key: `Source ID` is observed unique and non-null.
- Foreign keys: none.
- Required fields: ID, name, and type are populated.
- Unique constraints: ID and name are observed unique.
- Known problems: operational and lifecycle fields are entirely empty.

**Temporary adapter contract**

Identity mapping; preserve unknown values as null.

**Canonical target schema**

Retain columns with typed Boolean/date fields. Require ID, name, type, active state,
and requires-internet state after backfill.

**Migration notes**

Define licensing and internet requirements before enforcing fields.

### `repair_guides` / `tblRepairGuides`

**Current workbook schema**

- Columns and observed types: `Guide ID`, `Device ID`, `Manufacturer`, `Device Family`,
  `Device Name`, `Service ID`, `Service Name`, and `Guide Category` are str/empty;
  `Document Type`, `Guide Title`, `Guide Format`, `Source`, `Embed URL`, `Local File`,
  `Difficulty`, `Standard Labor`, `Skill Level`, `Active`, `Last Verified`, `Guide
  Status`, and `Notes` are entirely empty.
- Primary key: `Guide ID` is observed unique and non-null, including blank-content
  guide rows.
- Foreign keys: populated `Device ID` -> master devices and `Service ID` -> master
  services are inferred. Category and source use descriptions rather than IDs.
- Required fields: only guide ID is universally populated; 456 rows lack device,
  service, and descriptive data.
- Unique constraints: guide ID is observed unique.
- Known problems: 456 largely empty records with generated IDs; duplicated descriptive
  columns; category/source not normalized; no title or content/location data.

**Temporary adapter contract**

Treat rows without a device/service/content reference as incomplete, not active
guides. Do not silently delete them.

**Canonical target schema**

`Guide ID`, `Device ID` (nullable only for family/global guides), `Device Family Code`,
`Service ID`, `Category ID`, `Source ID`, `Guide Title`, `Document Type`, `Guide
Format`, `Embed URL`, `Local File`, `Difficulty`, `Standard Labor`, `Skill Level`,
`Active`, `Last Verified`, `Guide Status`, `Notes`.

**Migration notes**

Define global/family/device guide scope before setting required fields. Map category
and source descriptions to IDs.

### `technical_library` / `tblTechnicalLibrary`

**Current workbook schema**

- Columns: `Technical ID`, `Resource Type ID`, `Resource Type`, `Device ID`, `Device
  Name`, `Manufacturer`, `Device Family`, `Service ID`, `Service Name`, `Category ID`,
  `Category Name`, `Reference ID`, `Source ID`, `Source Name`, `Resource Title`,
  `Version`, `Active`, `Last Verified`, `Created Date`, `Modified Date`, `Notes`.
- Observed types: all columns are empty across two placeholder rows.
- Primary/foreign keys, required fields, and unique constraints: suggested by names
  but unsupported by populated evidence.
- Known problems: blank placeholder records and extensive denormalized descriptions.

**Temporary adapter contract**

Treat fully blank rows as no records. No other adapter is approved.

**Canonical target schema**

Unresolved pending the technical-library workflow. Likely identifiers must not be
treated as approved constraints until resource types and references are defined.

**Migration notes**

Do not invent records or relationships from column names alone.

### `parts_catalog` / `tblPartsCatalog`

**Current workbook schema**

- Columns: `Manufacturer`, `Device Type`, `Device Family`, `Device Model`, `Service
  Type`, `Labor`, `Parts`, `Final Price`, `Square Item Name`, `SKU`.
- Observed types: all values are empty in one placeholder row.
- Primary key: `SKU` is inferred but unpopulated.
- Foreign keys, required fields, and uniqueness: undefined.
- Known problems: this is a pricing/export catalog, not an inventory ledger; there is
  no `Quantity` column although inventory code expects it.

**Temporary adapter contract**

Treat the blank row as no catalog item. Inventory operations must return an explicit
configuration/unavailable error rather than fabricate quantity.

**Canonical target schema**

The catalog's final design is unresolved. Inventory quantity belongs in planned
`inventory_items`, not this table.

**Migration notes**

Separate catalog, cost, retail-output, and inventory responsibilities before
populating this table.

### `supplier_catalog` / `tblSupplierCatalog`

**Current workbook schema**

- Columns and observed types: `Supplier` (str), `Website` (str), `Notes` (empty).
- Primary key: none. Supplier name is observed unique.
- Foreign keys: none.
- Required fields: supplier and current website field are populated.
- Unique constraints: supplier name is observed unique; not enforced.
- Known problems: values in `Website` are descriptions such as supplier role, not URL
  values; two values are duplicated.

**Temporary adapter contract**

Expose `Website` as untrusted legacy text; do not render it as a URL without URL
validation.

**Canonical target schema**

Proposed columns: `Supplier ID`, `Supplier Name`, `Website`, `Active`, `Notes`.
Additional contact fields require business requirements.

**Migration notes**

Generate stable IDs only during an approved migration; move descriptive legacy text
to notes after human review.

### `labor_rates` / `tblLaborRates`

**Current workbook schema**

- Columns and observed types: `Service Type` (str), `Labor Price` (int), `Estimated
  Time` (int).
- Primary key: none. `Service Type` is observed unique for 10 rows.
- Foreign keys: service type appears descriptive; it does not reference
  `master_services.Service ID`.
- Required fields: all are populated.
- Unique constraints: service type is observed unique.
- Known problems: pricing engine expects absent `Hourly Rate`; units for `Labor Price`
  are ambiguous; estimated time appears to be minutes but is not labeled; no effective
  dates or active state.

**Temporary adapter contract**

Expose `Labor Price` as `Legacy Labor Price` until fixed-charge versus hourly semantics
are approved. Expose `Estimated Time` as minutes only if confirmed by the owner.

**Canonical target schema**

`Labor Rate ID`, `Service ID`, `Hourly Rate`, `Effective From`, `Effective To`,
`Active`. Estimated duration should live in master services with an explicit unit.

**Migration notes**

Do not rename `Labor Price` to `Hourly Rate` until its meaning is confirmed. Map
descriptive service types to stable service IDs.

### `parts_pricing` / `tblParts`

**Current workbook schema**

- Columns and observed types: `Manufacturer`, `Device Model`, and `Part` are str/empty;
  `Cost` is float/empty. One populated row and two blank rows exist.
- Primary key: none.
- Foreign keys: manufacturer and device model are descriptive, not stable IDs.
- Required fields: undefined; the populated row has all four values.
- Unique constraints: none evidenced.
- Known problems: no SKU, supplier, effective date, active state, or stable key; blank
  rows included.

**Temporary adapter contract**

Drop fully blank rows in read views. Expose `Cost` as a decimal-compatible value but
do not change workbook storage.

**Canonical target schema**

`SKU`, `Supplier ID` (nullable), `Unit Cost`, `Effective From`, `Effective To`,
`Active`.

**Migration notes**

Create SKU relationships before replacing manufacturer/model/part descriptions.

### `retail_pricing` / `tblRetailPricing`

**Current workbook schema**

- Columns and observed types: `Service Type` (empty), `Labor` (float/empty), `Part`
  (float/empty), `Processing Fees` (int), `Retail` (int).
- Primary/foreign keys: none.
- Required fields and unique constraints: undefined.
- Known problems: mostly blank/default rows; pricing engine expects missing `Markup`;
  table appears to mix calculated inputs and output without identifiers.

**Temporary adapter contract**

Do not use this table as a markup-rule source. Treat it as incomplete legacy output.

**Canonical target schema**

Unresolved as an output table. Pricing rules belong in planned `pricing_rules`.
If retail-pricing persistence remains, it requires an ID, quote/ticket relationship,
input amounts, calculated total, rule version, and timestamp.

**Migration notes**

Decide whether to retire or redefine this table after pricing rules are approved.

### `profit_margin` / `tblProfitMargin`

**Current workbook schema**

- Columns and observed types: `Supplier` (str), `Part Name` (empty), `Supplier SKU`
  (empty), `Supplier Cost` (int), `Labor Cost` (int), `Processing Fee 1%` (float),
  `Profit Margin %` (float/empty), `Retail Part Markup` (int), `Final Price` (float).
- Primary key: none.
- Foreign keys: supplier is descriptive and not a stable supplier ID.
- Required fields and unique constraints: undefined.
- Known problems: mixes examples, rule inputs, calculated outputs, percentages, and
  amounts; `Processing Fee 1%` contains both `0.01` and approximately `7.0`, indicating
  incompatible units; one supplier row is named `Testing`.

**Temporary adapter contract**

Do not use as an authoritative engine rule source. Preserve for analysis only.

**Canonical target schema**

Retire or migrate approved rule fields into planned `pricing_rules`; calculated
results belong with quotes/pricing records. Exact migration depends on resolving unit
semantics.

**Migration notes**

Each row requires human classification before any automated migration.

## Planned tables only

The following tables do not currently exist in `config.database.TABLES` and must not
be treated as loaded functionality.

### Planned `inventory_items`

Proposed columns: `SKU`, `Quantity On Hand`, `Quantity Reserved`, `Reorder Level`,
`Active`, `Last Updated`. Proposed PK/unique constraint: `SKU`. Available quantity is
proposed as on-hand minus reserved. This rule remains subject to approval.

### Planned `pricing_rules`

Proposed columns: `Pricing Rule ID`, `Service ID` (nullable for a default), `Parts
Markup Multiplier`, `Processing Fee Rate`, `Minimum Labor Charge`, `Effective From`,
`Effective To`, `Active`. Exact rule precedence remains unresolved.

## Cross-table relationship summary

These relationships are inferred or proposed, not enforced:

| Child field | Parent field | Confidence |
|---|---|---|
| `customer_devices.Customer ID` | `customers.Customer ID` | High by name; no populated child evidence. |
| `repair_tickets.Customer ID` | `customers.Customer ID` | High by name; no populated ticket evidence. |
| `repair_tickets.Device ID` | customer-device identifier | Ambiguous because both customer and master devices use device terminology. |
| `master_devices.Manufacturer Code` | `manufacturer_catalog.Manufacturer ID` | High. |
| `master_devices.Device Family Code` | `device_catalog.Device Family Code` | High. |
| `compatibility.Device Family` | `device_catalog.Device Family Code` | High; mislabeled child field. |
| `compatibility.Service Name` | `master_services.Service ID` | High; values are service IDs. |
| `repair_guides.Device ID` | `master_devices.Device ID` | High. |
| `repair_guides.Service ID` | `master_services.Service ID` | High. |
| technical-library ID fields | corresponding catalogs | Low; no populated evidence. |

## Unresolved schema questions

1. Is `labor_rates.Labor Price` an hourly rate or a fixed service charge?
2. Is `labor_rates.Estimated Time` measured in minutes?
3. Should `service_types` remain a separate lookup, and how does it map to master
   services?
4. What is the canonical identifier for a customer-owned device versus a master device?
5. Should `retail_pricing` be retired, or should it store calculated quote results?
6. Which `profit_margin` fields are rules versus example/calculated outputs, and what
   are their units?
7. What table will own part/device compatibility and canonical SKU assignment?
8. What fields and lifecycle define a diagnostic record?
9. What constitutes a valid active repair guide, and are family/global guides allowed?
10. What duplicate policy applies to customer email and phone numbers?

No workbook columns should be renamed and no constraints should be enforced until
these questions are resolved, adapter tests exist, and a backed-up migration is
approved.
