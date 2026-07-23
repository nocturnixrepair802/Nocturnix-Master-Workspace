# Master Compatibility Catalog V1 Data Dictionary

## Authority and Schema

This dictionary implements
`Documentation/ADR/ADR-010-master-compatibility-governance.md`.
`tblMasterCompatibilityCatalog` contains exactly 31 columns in the order below.
Blank means unknown or not applicable; it never means approved.

| # | Field | Type | Req. | Source | Valid values / lookup | Transformation and validation | Business meaning |
|---:|---|---|---|---|---|---|---|
| 1 | Compatibility ID | Text | Yes | Generated / canonical namespace | `^CMP\d{6}$` | Runtime continuation; unique, continuous, immutable, no overlap | Review relationship identity |
| 2 | Relationship Type | Text | Yes | Evidence result | `DV_RelationshipTypes` | Must agree with target and level fields | Kind and endpoint scope |
| 3 | Device ID | Text | Conditional | Master Devices | `DV_DeviceIDs` | Required for model/variant; blank for family | Device model endpoint |
| 4 | Device Family Code | Text | Conditional | Source catalogs / Master Devices | `DV_DeviceFamilyCodes` | Required for family and reconciled when populated | Device taxonomy endpoint |
| 5 | Device Variant | Text | Conditional | Master Devices | Free text | Required only for variant relationship | Variant endpoint |
| 6 | Service ID | Text | Conditional | Master Services | `DV_ServiceIDs` | Required for Service types; Part ID blank | Service endpoint |
| 7 | Part ID | Text | Conditional | Master Parts | `DV_PartIDs` | Required for Part types; Service ID blank | Part endpoint |
| 8 | Manufacturer ID | Text | Optional | Referenced catalog row | `DV_ManufacturerIDs` | Must reconcile when populated | Manufacturer reference |
| 9 | Manufacturer Name | Text | Optional | Referenced catalog row | Lookup text | Preserved; no guessed manufacturer | Display/evidence context |
| 10 | Device Name | Text | Conditional | Master Devices | Lookup text | Must match Device ID; blank for family-only | Device display context |
| 11 | Service Name | Text | Conditional | Master Services | Lookup text | Required for Service target | Service display context |
| 12 | Part Name | Text | Conditional | Master Parts | Lookup text | Required for Part target | Part display context |
| 13 | Compatibility Level | Text | Yes | Evidence result | `DV_CompatibilityLevels` | Must agree with Relationship Type | Family/model/variant granularity |
| 14 | Compatibility Status | Text | Yes | Generated lifecycle | `DV_CompatibilityStatuses` | Generated value is Proposed | Compatibility lifecycle |
| 15 | Evidence Type | Text | Yes for Proposed | Evidence rule | `DV_EvidenceTypes` | Cannot be blank for proposal | Strongest evidence class |
| 16 | Evidence Source | Text | Yes for Proposed | Source path/sheet | ASCII-safe text | Names the protected source | Evidence provenance |
| 17 | Evidence Detail | Text | Yes for Proposed | Generated explanation | ASCII-safe text | Must describe exact rule, not a conclusion | Auditable rationale |
| 18 | Confidence | Text | Yes | Evidence tier | `DV_ConfidenceValues` | High/Medium/Low/Unassessed | Evidence confidence, not approval |
| 19 | Requires Manual Review | Text | Yes | Generated policy | `DV_YesNo` | Yes for all inferred/family records | Human review gate |
| 20 | Active | Text | Yes | Generated policy | `DV_YesNo` | Generated value is No | Whether approved for use |
| 21 | Effective Date | Date | Optional | Reviewer | `yyyy-mm-dd` | Blank until governed approval | Relationship start |
| 22 | Expiration Date | Date | Optional | Reviewer | `yyyy-mm-dd` | Must not precede Effective Date | Relationship end |
| 23 | Review Status | Text | Yes | Generated lifecycle | `DV_ReviewStatuses` | Never generated Approved/Ready for Approval | Review workflow |
| 24 | Reviewer | Text | Optional | Reviewer | Free text | Blank initially | Accountable reviewer |
| 25 | Reviewer Notes | Text | Optional | Reviewer | Free text | No invented outcome | Review rationale |
| 26 | Source Record Number | Integer/Text | Optional | Target source | Source value | Preserved for deterministic ordering | Source row lineage |
| 27 | Source Workbook | Text | Yes | Target source | Protected path/name | Preserved | Source artifact |
| 28 | Source Worksheet | Text | Yes | Target source | Protected sheet | Preserved | Source location |
| 29 | Import Batch ID | Text | Yes | Generator | `MASTER-COMPATIBILITY-V1-REVIEW` | Constant | Review batch lineage |
| 30 | Created At | DateTime/Text | Optional | Target source | Excel-safe value | Aware datetime becomes naive UTC | Source creation observation |
| 31 | Updated At | DateTime/Text | Optional | Target source | Excel-safe value | Aware datetime becomes naive UTC | Source update observation |

## Controlled Values

Relationship Type values are Device to Service, Device to Part, Device Family
to Service, Device Family to Part, Device Variant to Service, and Device
Variant to Part.

Compatibility Level values are Family Level, Model Level, Variant Level,
Universal, Not Applicable, and Unresolved.

Evidence Type values are Explicit Source Match, Canonical Relationship, Exact
Model Match, Exact Manufacturer and Model, Family-Level Evidence, Legacy Name
Evidence, Manual Research Required, and No Reliable Evidence.

Compatibility Status values are Pending Review, Proposed, Confirmed, Rejected,
and Archived. Review Status values are Pending Review, Pending Evidence Review,
Pending Device Review, Pending Service Review, Pending Part Review, Ready for
Approval, Approved, Rejected, and Archived. Confidence values are Unassessed,
Low, Medium, and High. Boolean values are Yes and No.

## Unresolved Review Schema

`tblCompatibilityUnresolvedReview` contains exactly: Candidate Type, Device ID,
Device Family Code, Device Name, Service ID, Service Name, Part ID, Part Name,
Missing Evidence, Ambiguity Reason, Required Action, Review Priority, Review
Status, and Reviewer Notes. Rows preserve uncertainty and never record an
invented outcome.

## Prohibited Fields

The primary schema excludes price, cost, supplier cost, stock, quantity,
inventory, margin, and final approval fields. Those domains remain governed by
their own catalogs and workflows.
