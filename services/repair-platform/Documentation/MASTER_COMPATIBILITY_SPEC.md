# Master Compatibility Catalog V1 Specification

## Authority and Purpose

This specification implements
`Documentation/ADR/ADR-010-master-compatibility-governance.md`.
Master Compatibility Catalog V1 is a standalone review framework for governed
relationships among Devices, Device Families, Device Variants, Services, and
Parts. Compatibility records are relationship records; they do not create or
change a device, service, or part identity.

Planned review outputs:

- `D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Compatibility_Catalog_v1.xlsx`
- `D:\Business Portal\300_Pricing\Working\Nocturnix_Compatibility_Relationship_Audit_v1.xlsx`

Neither output is a canonical import. The generators and validator never save
an input workbook or write to the canonical database.

## Scope and Boundary

The controlled relationship types are:

- Device to Service
- Device to Part
- Device Family to Service
- Device Family to Part
- Device Variant to Service
- Device Variant to Part

The controlled granularities are Family Level, Model Level, Variant Level,
Universal, Not Applicable, and Unresolved.

The catalog does not own identity, inventory, stock, supplier cost, quantity,
pricing, repair tickets, or automatic approval. Relationship approval does not
approve pricing or inventory availability.

## Source Precedence

All inputs are read-only and protected by SHA-256 hashes before and after a
workflow:

1. Master Devices owns Device ID, family, variant, manufacturer, and device
   display evidence.
2. Master Services owns Service ID, device applicability observations, repair
   type, service name, and provenance.
3. Master Parts owns Part ID, device applicability observations,
   compatibility scope, part type, part name, and provenance.
4. Canonical `35 Compatibility Matrix` owns only the existing Compatibility ID
   namespace and existing canonical relationship evidence.
5. The legacy deduplication proposal identifies excluded source rows that may
   not re-enter the population.
6. Master Pricing is protected for noninterference; it supplies no
   compatibility fact.

When sources disagree, the conflict is unresolved. A weaker source never
overrides a stronger identity or explicit relationship field.

## Identity and ID Allocation

ADR-010 approves `CMP######` with regex `^CMP\d{6}$`. At runtime:

- locate the `Compatibility ID` header in `35 Compatibility Matrix`;
- accept only regex-valid values for sequence arithmetic;
- reject duplicate valid canonical IDs;
- report malformed populated values separately;
- continue after the highest valid ID, or begin at `CMP000001` for a valid
  empty namespace;
- never reuse or renumber an ID; and
- allocate continuously after deterministic ordering by Relationship Type,
  Device ID, target ID, Source Record Number, then family code.

Read-only inspection on 2026-07-23 found 82 valid IDs from `CMP000001` through
`CMP000082`, no duplicates, no malformed values, and no gaps. The expected
first generated ID is therefore `CMP000083`.

## Evidence Hierarchy and Candidate Generation

The generator selects one best supported tier for each source target:

1. **Tier 1:** explicit valid Device ID in the source, or an exact device-name
   or model match with explicit manufacturer agreement.
2. **Tier 2:** exact manufacturer, family, and normalized model-token match.
   Tokens must identify the whole model; subset and fuzzy similarity do not
   qualify.
3. **Tier 3:** explicit family applicability with no defensible model match.
4. **Below Tier 3:** no relationship record. Preserve a useful candidate in
   Unresolved Review.

Manufacturer-only agreement, family coincidence without an explicit source
family, the word `phone`, and vague or generic names are insufficient for a
model relationship. Generic part names such as Battery, Camera, Charging Port,
and Screen Adhesive require explicit device or family evidence.

Service candidates use Service ID, Manufacturer, Device Family, Device Series,
Device Model, Repair Type, and Service Name. Part candidates use Part ID,
Manufacturer, Device Family, Device ID, Device Name, Compatibility Scope, Part
Type, and Part Name.

Family-only service evidence produces `Device Family to Service`, Family
Level, Proposed, Requires Manual Review = Yes, and Active = No. Family-only
part evidence follows the equivalent Part rule. A model result is never
produced from family-only evidence.

## Duplicate Relationship Rules

A relationship key is:

- Relationship Type;
- Device ID or Device Family Code;
- Service ID or Part ID; and
- Device Variant where applicable.

Exact duplicate keys are rejected. Relationships with different evidence or
granularity are not silently merged. Candidate generation chooses the strongest
single supported granularity for a target; it does not emit both family and
model rows for the same target unless a future approved specification
explicitly requires both.

## Status Lifecycle

Compatibility Status values are Pending Review, Proposed, Confirmed, Rejected,
and Archived. Generated relationships are Proposed.

Review Status values are Pending Review, Pending Evidence Review, Pending
Device Review, Pending Service Review, Pending Part Review, Ready for Approval,
Approved, Rejected, and Archived. Generated relationships begin Pending Review
or an applicable pending subtype. No generated record is Confirmed, Approved,
or Ready for Approval. Active defaults to No. Inferred relationships require
manual review.

## Workbook Contract

The primary schema has exactly 31 columns as documented in
`MASTER_COMPATIBILITY_DATA_DICTIONARY.md`.

| Order | Worksheet | Excel Table |
|---:|---|---|
| 1 | 00 - Instructions | `tblMasterCompatibilityInstructions` |
| 2 | 01 - Compatibility Records | `tblMasterCompatibilityCatalog` |
| 3 | 02 - Relationship Types | `tblCompatibilityRelationshipTypes` |
| 4 | 03 - Compatibility Levels | `tblCompatibilityLevels` |
| 5 | 04 - Evidence Types | `tblCompatibilityEvidenceTypes` |
| 6 | 05 - Devices | `tblCompatibilityDevices` |
| 7 | 06 - Services | `tblCompatibilityServices` |
| 8 | 07 - Parts | `tblCompatibilityParts` |
| 9 | 08 - Family Relationships | `tblCompatibilityFamilyReview` |
| 10 | 09 - Model Relationships | `tblCompatibilityModelReview` |
| 11 | 10 - Variant Relationships | `tblCompatibilityVariantReview` |
| 12 | 11 - Unresolved Review | `tblCompatibilityUnresolvedReview` |
| 13 | 12 - Validation Summary | `tblMasterCompatibilityValidation` |
| 14 | 13 - Revision History | `tblMasterCompatibilityRevisionHistory` |
| 15 | 14 - Import Metadata | `tblMasterCompatibilityImportMetadata` |

All 15 names are unique and no longer than 31 characters. Every populated
sheet contains exactly one table with filters and a frozen header.

## Defined Names

All cross-sheet list validations use workbook-scoped names:

- `DV_RelationshipTypes`
- `DV_CompatibilityLevels`
- `DV_CompatibilityStatuses`
- `DV_EvidenceTypes`
- `DV_ReviewStatuses`
- `DV_DeviceIDs`
- `DV_DeviceFamilyCodes`
- `DV_ServiceIDs`
- `DV_PartIDs`
- `DV_ManufacturerIDs`
- `DV_ConfidenceValues`
- `DV_YesNo`

Direct cross-sheet list formulas and hard-coded comma-separated governed lists
are prohibited.

## Review Queues

Pending relationship rows appear exactly once in Family, Model, or Variant
Relationships according to Compatibility Level. Unresolved Review contains
candidate identity, missing evidence, ambiguity, required action, priority,
status, and notes. A queue never invents an outcome.

The relationship audit is deliberately separate. It records the best evidence,
runner-up score, margin, coverage, match detail, proposed level/status, mapping
result, failure reason, and manual-review flag. Audit rows are not copied into
the Master Compatibility workbook automatically.

## Ownership

- Compatibility rules and approval: Repair Engineering.
- Device identity and taxonomy: Product Catalog.
- Service identity: Repair Engineering.
- Part identity and applicability: Procurement and Repair Engineering.
- Workbook construction, validation, and protected-file controls: Data
  Engineering.
- Pricing, cost, and inventory remain owned by their separate governance
  domains.

## Import Prohibition and Known Limitations

A passing workbook validates a review artifact only. Canonical import requires
separate authorization and must not be inferred from this milestone.

Known limitations:

- legacy manufacturer fields are incomplete and sometimes contain product-line
  labels;
- explicit variant applicability is sparse;
- family evidence can be broad and always requires review;
- canonical compatibility rows are legacy-shaped and are used for namespace
  discovery, not silently remapped into the proposed population;
- name normalization is conservative and intentionally produces false
  negatives rather than unsafe precise matches; and
- pricing, inventory availability, supplier evidence, and repair capability
  are outside this specification.
