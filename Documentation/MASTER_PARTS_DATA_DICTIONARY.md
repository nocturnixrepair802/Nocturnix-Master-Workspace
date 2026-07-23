# Master Parts Catalog V1 Data Dictionary

ADR-008 accepts this exact 50-column `tblMasterPartsCatalog` schema.

| Field | Type | Req. | Source / transformation | Meaning and validation | Blank / zero semantics |
|---|---|---:|---|---|---|
| Part ID | Text | Yes | ADR-008; next `PRT######` | Proposed immutable identity; unique and continuous | Blank prohibited |
| Legacy Part SKU | Text | No | Copy Legacy SKU | Alias/reference only | Blank preserved |
| Active | Text | Yes | Default Yes | Proposed active flag; Yes/No | Not approval |
| Status | Text | Yes | Default Draft | Part lifecycle | No generated Approved |
| Part Name | Text | Yes | Copy Legacy Name | Identity label | Blank prohibited |
| Part Display Name | Text | Yes | Copy Legacy Name | Review display label | Blank prohibited |
| Part Description | Text | No | Copy Legacy Note only | Source-supported description | Blank when absent |
| Part Category ID | Text | Yes | Deterministic proposed ID from Legacy Group | Category relationship | Blank prohibited |
| Part Category | Text | Yes | Copy Legacy Group | Proposed category | Blank prohibited |
| Part Type ID | Text | Yes | Deterministic proposed ID from Legacy Type | Type relationship | Blank prohibited |
| Part Type | Text | Yes | Copy Legacy Type | Proposed type | Blank prohibited |
| Manufacturer ID | Text | Conditional | Exact canonical name match | Manufacturer relationship | Blank pending review |
| Manufacturer Name | Text | No | Copy Legacy Manufacturer | Source observation | Blank preserved |
| Device Family Code | Text | No | Conservative explicit type mapping | Family applicability | Blank unresolved |
| Device Family Name | Text | No | Canonical family name | Family label | Blank with no mapping |
| Device ID | Text | No | Exact evidence only | Device-specific applicability | Blank in generated V1 |
| Device Name | Text | No | Canonical device label | Device relationship label | Blank with Device ID |
| Compatibility Scope | Text | No | Reviewer | Proposed applicability scope | Blank unresolved |
| Part Quality | Text | No | Reviewer | Quality taxonomy | Blank; never inferred |
| Condition | Text | No | Copy Legacy Condition | Source condition observation, not identity | Blank preserved |
| OEM Status | Text | No | Reviewer | OEM/aftermarket classification | Blank; never inferred |
| Color | Text | No | Reviewer/source evidence | Variant attribute | Blank; never inferred |
| Capacity | Text | No | Reviewer/source evidence | Variant attribute | Blank; never inferred |
| Model Number | Text | No | Reviewer/source evidence | Manufacturer part/model reference | Blank; never inferred |
| Supplier ID | Text | No | Approved supplier lookup only | Sourcing relationship | Blank without approved ID |
| Supplier Name | Text | No | Copy Legacy Supplier | Provisional supplier observation | Blank preserved |
| Supplier Part Number | Text | No | Supplier evidence | Supplier-specific reference | Blank; never inferred |
| Preferred Supplier | Text | Yes | Default No | Proposed preference flag | No is not rejection |
| Legacy Retail Price | Decimal/text | No | Exact source observation | Historical/provisional retail | Zero preserved; blank distinct |
| Legacy Cost | Decimal/text | No | Exact source observation | Historical/provisional cost | Zero is not verified; blank distinct |
| Currency | Text | No | Future policy | Currency code | Blank; no default |
| Cost Status | Text | Yes | Derived from observation | Cost review lifecycle | Zero still Legacy Cost Only |
| Pricing Status | Text | Yes | Derived from observation | Pricing review lifecycle | No approval |
| Inventory Tracked | Text | Yes | Default Yes | Proposed inventory integration flag | Does not create inventory |
| Serialized | Text | Yes | Default No | Proposed serialization flag | No unless evidence |
| Warranty Eligible | Text | Yes | Default No | Proposed warranty flag | No until review |
| Default Warranty | Text | No | Reviewer | Warranty option | Blank until approved |
| Compatibility Status | Text | Yes | Conservative mapping | Compatibility workflow | Pending when unresolved |
| Sourcing Status | Text | Yes | Supplier observation rule | Sourcing workflow | Unknown when blank |
| Review Status | Text | Yes | Most restrictive unresolved rule | Overall review workflow | No preapproval |
| Source Record Number | Integer | Yes | Copy Source Row Number | Unique provenance and ordering | Positive, unique |
| Source Workbook | Text | Yes | Copy proposal source workbook | Original source provenance | Blank prohibited |
| Source Worksheet | Text | Yes | Copy proposal source worksheet | Original source sheet | Blank prohibited |
| Import Batch ID | Text | Yes | `MASTER-PARTS-V1-REVIEW` | Generation batch | Blank prohibited |
| Reviewer | Text | No | Reviewer | Review owner | Blank initially |
| Reviewer Notes | Text | No | Copy Legacy Note/reviewer | Source/review context | Blank preserved |
| Effective Date | Date | No | Future approval | Canonical effective date | Blank initially |
| Last Reviewed | Date | No | Reviewer | Review audit date | Blank initially |
| Created At | Date/time or text | No | Copy Source Created At | Source provenance | Blank/text preserved |
| Updated At | Date/time or text | No | Copy Source Updated At | Source provenance | Blank/text preserved |

## Controlled Values

Part Status: Draft, Active, Planned, Future, Archived, Rejected.

Review Status: Pending Review, Pending Manufacturer Review, Pending Device
Mapping, Pending Compatibility Review, Pending Sourcing Review, Pending Cost
Review, Ready for Approval, Approved, Rejected, Archived.

Compatibility Status: Pending Compatibility Review, Device Family Only, Device
Specific, Universal, Not Applicable, Approved, Rejected.

Sourcing Status: Pending Sourcing Review, Supplier Unknown, Supplier Observed,
Multiple Suppliers, Preferred Supplier Proposed, Approved, Rejected.

Cost Status: Pending Cost Review, Legacy Cost Only, Supplier Cost Required,
Landed Cost Required, Ready for Cost Approval, Approved, Rejected.

Pricing Status: Pending Pricing Review, Legacy Price Review, Not for Direct Sale,
Ready for Pricing Review, Approved, Rejected.

Boolean-style fields use Yes or No. Generated values are review defaults, not
approved canonical policies.

## Proposed Lookup Identity

Part Category IDs and Part Type IDs are deterministic proposal-local lookup IDs
derived from sorted unique legacy values. They support review and validation but
do not authorize canonical import.

Manufacturer, device-family, and device IDs come only from canonical read-only
lookups. Canonical Suppliers currently have no Supplier ID column, so generated
Supplier ID remains blank while Supplier Name preserves the observation.
