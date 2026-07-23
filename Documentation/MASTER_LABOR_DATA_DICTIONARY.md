# Master Labor Catalog V1 Data Dictionary

## Authority and Schema

This dictionary implements
`Documentation/ADR/ADR-011-master-labor-standards-governance.md`.
`tblMasterLaborCatalog` contains exactly 31 columns in the order below. Blank
means unknown or not applicable; it never means approved.

| # | Field | Type | Req. | Source | Valid values / lookup | Transformation and validation | Business meaning |
|---:|---|---|---|---|---|---|---|
| 1 | Labor Standard ID | Text | Yes | Generated namespace | `^LAB\d{6}$` | Unique, continuous, ordered, nonoverlapping | Review labor identity |
| 2 | Legacy Labor ID | Text | Optional | Protected Labor Standards | Source text | Preserved exactly as lineage | Previous identifier |
| 3 | Labor Name | Text | Yes | Source labor name/service | Source text | Copy only; nonblank | Labor activity label |
| 4 | Repair Category | Text | Optional | Source | `DV_LaborRepairCategories` | Exact observed value only | Broad repair grouping |
| 5 | Repair Type | Text | Optional | Source | `DV_LaborRepairTypes` | Exact observed value only | Repair activity type |
| 6 | Device Family | Text | Optional | Source | `DV_LaborDeviceFamilies` | Exact observed value only | Applicable family |
| 7 | Manufacturer | Text | Optional | Source | `DV_LaborManufacturers` | Exact observed value only | Applicable manufacturer |
| 8 | Standard Minutes | Integer | Optional | Source | Positive integer | No inference; within bounds | Expected duration |
| 9 | Minimum Minutes | Integer | Optional | Source | Nonnegative integer | `Minimum <= Standard` when both exist | Lower duration bound |
| 10 | Maximum Minutes | Integer | Optional | Source | Positive integer | `Standard <= Maximum` when both exist | Upper duration bound |
| 11 | Labor Tier | Text | Optional | Source | `DV_LaborTiers` | Copy only | Governed labor tier |
| 12 | Skill Level | Text | Optional | Source | `DV_LaborSkillLevels` | Copy only | Expected skill |
| 13 | Difficulty | Text | Optional | Source | `DV_LaborDifficulties` | Copy only | Repair complexity |
| 14 | Warranty Option | Text | Optional | Source | `DV_LaborWarrantyOptions` | Copy only | Labor warranty observation |
| 15 | Requires Calibration | Text | Optional | Source | `DV_YesNo` | No inference | Calibration requirement |
| 16 | Requires Waterproof Test | Text | Optional | Source | `DV_YesNo` | No inference | Seal-test requirement |
| 17 | Requires Programming | Text | Optional | Source | `DV_YesNo` | No inference | Programming requirement |
| 18 | Requires Pairing | Text | Optional | Source | `DV_YesNo` | No inference | Pairing requirement |
| 19 | Requires Board Repair | Text | Optional | Source | `DV_YesNo` | No inference | Board-repair requirement |
| 20 | Special Tools Required | Text | Optional | Source | Source text | Blank, No, Yes, or explicit tool text | Tool requirement |
| 21 | Technician Certification | Text | Optional | Source | Source text | Copy only | Required credential |
| 22 | Review Status | Text | Yes | Generated/reviewer | `DV_LaborReviewStatuses` | Generated value Pending Review | Governance lifecycle |
| 23 | Confidence | Text | Yes | Source/reviewer | `DV_LaborConfidence` | Blank source becomes Unassessed | Evidence confidence |
| 24 | Source Record Number | Integer/Text | Yes | Source row/field | Positive row lineage | Deterministic and unique | Source record lineage |
| 25 | Source Workbook | Text | Yes | Generator | Protected workbook name/path | Copy only | Source artifact |
| 26 | Source Worksheet | Text | Yes | Generator | Source sheet | Copy only | Source location |
| 27 | Import Batch | Text | Yes | Generator | `MASTER-LABOR-V1-REVIEW` | Constant | Review batch lineage |
| 28 | Reviewer | Text | Optional | Reviewer | Free text | Blank initially | Accountable reviewer |
| 29 | Reviewer Notes | Text | Optional | Reviewer/source notes | Free text | Source notes may be preserved | Review rationale |
| 30 | Created At | DateTime/Text | Optional | Source | Excel-safe value | Aware datetime becomes naive UTC | Creation observation |
| 31 | Updated At | DateTime/Text | Optional | Source | Excel-safe value | Aware datetime becomes naive UTC | Update observation |

## Schema correction

The requested field list contains 31 fields, not 30. The authoritative primary
schema is therefore exactly 31 columns; no additional governance column was
added. The workbook contract and validators use all 31 fields shown above.

## Controlled Values

Review Status values are Pending Review, Pending Evidence Review, Ready for
Approval, Approved, Rejected, and Archived. Generated rows use Pending Review.
Confidence values are Unassessed, Low, Medium, and High. Boolean values are Yes
and No.

Repair categories, repair types, device families, manufacturers, labor tiers,
skill levels, difficulties, and warranty options are constructed only from
distinct populated source observations. Their presence in a lookup is not
approval.

## Review Queue Schema

`tblLaborReviewQueue` contains Labor Standard ID, Labor Name, Missing Evidence,
Relationship Issue, Required Action, Review Status, Reviewer, and Reviewer
Notes. It exposes uncertainty and never fills a missing labor fact.

## Prohibited Fields

The primary schema excludes labor rate, labor cost, customer price, payroll,
technician schedule, time-clock events, work completion, inventory, parts
cost, and automatic approval.
