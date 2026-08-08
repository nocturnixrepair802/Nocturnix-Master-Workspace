# Service Type Alias Data Dictionary

## Canonical Service Type snapshot

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| Proposed Canonical Service Type ID | Text | Yes | Governed or review-local `^STY\d{6}$`; unique |
| Service Category | Source value | As observed | Preserve detailed L:T value |
| Service Type | Text | Yes | Preserve; unique after exact normalization |
| Service Description | Source value | As observed | Preserve |
| Applies To | Source value | As observed | Preserve |
| Estimated Time (Min) | Source value | As observed | Preserve; no calculation |
| Default Warranty (Days) | Source value | As observed | Preserve |
| Taxable | Source value | As observed | Preserve |
| Active | Source value | As observed | Preserve |
| Internal Notes | Source value | As observed | Preserve |
| Identity Authority | Text | Yes | Existing governed ID or ADR-012 review-local identity |
| Review Status | Text | Yes | Generated as `Pending Review` |
| Reviewer Notes | Text | No | Human review notes |

## Alias register

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| Alias ID | Text | Yes | Review identity `^STA\d{6}$`; unique |
| Source System | Text | Yes | Origin of candidate |
| Source Field | Text | Yes | Source column represented |
| Source Value | Text | Yes | Preserve candidate label |
| Normalized Source Value | Text | Yes | Case-folded alphanumeric tokens for exact comparison |
| Proposed Canonical Service Type ID | Text | Conditional | Valid snapshot ID; blank if unsafe/ambiguous |
| Proposed Canonical Service Type | Text | Conditional | Must pair exactly with proposed ID |
| Alias Rule Type | Controlled text | Yes | Defined-name validation |
| Evidence | Text | Yes | Explicit rationale and ambiguity |
| Confidence | Controlled text | Yes | Evidence strength, never approval |
| Review Status | Controlled text | Yes | Generated as `Pending Review` |
| Reviewer | Text | No | Accountable reviewer |
| Reviewer Notes | Text | No | Decision notes |

Alias Rule Type values are `Exact Match`, `Approved Synonym Candidate`,
`Broader-to-Specific Review`, `Device-Family-Specific`,
`Manufacturer-Specific`, and `No Safe Mapping`. The word “Approved” in the
candidate rule label describes the governed candidate category; it does not set
or imply an approved Review Status.

## Service normalization

The Service table contains the exact source Service ID/name, Repair Type
ID/value, Manufacturer ID/name, and Device Family code/name. The proposed
canonical ID/type pair is both populated or both blank. Mapping Method,
Mapping Evidence, Confidence, `Pending Review`, and Reviewer Notes describe the
proposal without changing source data.

## Labor normalization

The Labor table contains the exact governed Labor Standard ID, Legacy Labor ID,
Labor Name, Repair Type, Device Family, and Manufacturer. The proposed
canonical pair and review fields follow the same pair and status rules as
Service normalization.

## Service-to-Labor candidates

The candidate table preserves Service context and canonical pair. A unique
eligible Labor Standard provides governed and legacy identity, Labor Name, and
source duration fields. `Ambiguity Count` is a positive integer.

If `Ambiguity Count` is greater than one, Suggested Labor Standard ID, Legacy
Labor ID, Labor Name, and minute fields remain blank. Candidate Method and
Evidence state the exact governed constraints and candidate IDs.

## Unresolved review

Unresolved records identify the source record, current type, possible canonical
types and Labor Standards, ambiguity reason, missing evidence, required action,
priority, status, and notes. They are review tasks, not rejected records.

## Defined names

All list validation uses workbook-defined names:

- `DV_CanonicalServiceTypeIDs`
- `DV_CanonicalServiceTypes`
- `DV_AliasRuleTypes`
- `DV_MappingMethods`
- `DV_ConfidenceValues`
- `DV_ReviewStatuses`
- `DV_DeviceFamilyCodes`
- `DV_ManufacturerIDs`
- `DV_LaborStandardIDs`
- `DV_YesNoValues`

Direct cross-sheet validation formulas are prohibited.
