# Master Services Catalog Data Dictionary

Required means required for every generated service unless the validation rule
explicitly permits a pending lookup. Source values remain observations; blank
optional fields must not be invented.

| Field | Type | Req. | Source | Valid values | Transformation | Business meaning | Lookup | Validation |
|---|---|---:|---|---|---|---|---|---|
| Service ID | Text | Yes | Canonical ID worksheet plus generator | `SVC######`; regex `^SVC\d{6}$` | Highest valid existing ID plus one; continuous in source-row order | Proposed canonical identity | 34 Master Services | Unique, nonblank, not reused |
| Legacy Service SKU | Text | No | Retained.Legacy SKU | Source value | ASCII-safe text only | Legacy alias/reference | None | Must equal source |
| Active | Text | Yes | Rule | Yes, No | Default Yes | Proposed active flag | Status Values | Controlled value |
| Status | Text | Yes | Rule/review | Active, Planned, Future, Draft, Archived | Default Draft | Lifecycle status | Status Values | Controlled value |
| Manufacturer ID | Text | Conditional | Canonical/legacy lookup | Listed ID | Name-to-ID lookup | Manufacturer relationship | Manufacturers | Blank only pending |
| Manufacturer Name | Text | No | Retained.Legacy Manufacturer | Preserve | Human manufacturer label | Manufacturers | ID/name consistent |
| Device Family Code | Text | Conditional | Derived lookup | Listed code | Type/group/name mapping | Device family relationship | Device Families | Blank only pending |
| Device Family Name | Text | Conditional | Derived lookup | Listed name | Category-to-family mapping | Human family label | Device Families | Code/name consistent |
| Device Series | Text | No | Retained.Legacy Group | Preserve | ASCII-safe text | Legacy series/group context | None | Optional |
| Device Model | Text | No | Retained.Legacy Name | Preserve | ASCII-safe text | Device/model context | None | Optional |
| Service Category ID | Text | Yes | Rule | SC-REPAIR | Constant | Canonical category relationship | Service Categories | Valid lookup |
| Service Category | Text | Yes | Rule | Repair | Constant | Service domain | Service Categories | Must be Repair |
| Repair Type ID | Text | Yes | Derived lookup | `RT-####` | Deterministic legacy classification ID | Repair-type relationship | Repair Types | Valid lookup |
| Repair Type | Text | Yes | Legacy group/type/name | Preserve selected label | First populated classification | Repair classification | Repair Types | ID/name consistent |
| Service Name | Text | Yes | Retained.Legacy Name | Preserve | ASCII-safe text | Internal service name | None | Nonblank |
| Service Display Name | Text | Yes | Retained.Legacy Name | Preserve | Initially equals Service Name | Customer-facing draft label | None | Nonblank |
| Service Description | Text | Yes | Legacy Note/name | Preserve or provenance statement | No invented technical claims | Service definition | None | Nonblank |
| Labor Standard ID | Text | No | Labor match | Labor catalog ID | Conservative scored match | Labor relationship | Labor Standards | Valid when populated |
| Standard Minutes | Integer | No | Matched labor row | Positive integer | Copy only | Expected labor duration | Labor Standards | Positive with Labor ID |
| Minimum Minutes | Integer | No | Matched labor row | Nonnegative integer | Copy only | Lower labor bound | Labor Standards | `Min <= Standard` |
| Maximum Minutes | Integer | No | Matched labor row | Positive integer | Copy only | Upper labor bound | Labor Standards | `Standard <= Max` |
| Labor Tier | Text | No | Matched labor row | Listed tier | Copy only | Labor-rate tier reference | Labor Tiers | Valid when populated |
| Repair Difficulty | Text | No | Matched labor row | Listed level | Copy only | Technical complexity | Difficulty Levels | Valid when populated |
| Skill Level | Text | No | Matched labor row | Listed level | Copy only | Required technician skill | Skill Levels | Valid when populated |
| Turnaround Time | Text | Yes | Rule/review | Listed option | Default To Be Determined | Service fulfillment target | Turnaround Times | Valid lookup |
| Requires Parts | Text | Yes | Rule/review | Yes, No | Default Yes | Parts requirement | Status Values | Controlled value |
| Requires Labor | Text | Yes | Rule | Yes, No | Default Yes | Labor requirement | Status Values | Controlled value |
| Diagnostic Required | Text | Yes | Rule/review | Yes, No | Default No | Diagnostic prerequisite | Status Values | Controlled value |
| Warranty Eligible | Text | Yes | Rule/review | Yes, No | Default Yes | Warranty eligibility | Status Values | Controlled value |
| Default Warranty | Text | Yes | Rule/labor | Listed option | Default N/A | Proposed warranty option | Warranty Options | Valid lookup |
| Mobile Service Eligible | Text | Yes | Rule/review | Yes, No | Default No | Mobile-service eligibility | Status Values | Controlled value |
| Mail-In Eligible | Text | Yes | Rule/review | Yes, No | Default No | Mail-in eligibility | Status Values | Controlled value |
| Pricing Status | Text | Yes | Legacy observations | Four controlled statuses | Classify; do not price | Pricing-governance state | Status Values | Controlled value |
| Legacy Retail Price | Decimal/text | No | Retained.Legacy Retail Price | Exact source observation | Preserve; no calculation | Historical/provisional price | None | Never final price |
| Legacy Cost | Decimal/text | No | Retained.Legacy Cost | Exact source observation | Preserve; no calculation | Historical/provisional cost | None | Zero is permitted |
| Source Record Number | Integer | Yes | Retained.Source Row Number | Positive unique integer | Copy | Source provenance | None | Unique; retained only |
| Source Workbook | Text | Yes | Generator | Proposal filename | Constant | Provenance workbook | None | Nonblank |
| Source Worksheet | Text | Yes | Generator | 01 - Retained | Constant | Provenance worksheet | None | Exact value |
| Import Batch ID | Text | Yes | Generator | MASTER-SERVICES-V1-DRAFT | Constant | Draft generation batch | None | Nonblank |
| Review Status | Text | Yes | Rules/review | Controlled statuses | Derive gaps/conflicts | Readiness state | Status Values | Controlled value |
| Reviewer Notes | Text | No | Conflict/reviewer | Free text | Preserve reviewed note | Review rationale | None | Optional |
| Effective Date | Date | No | Future approval | ISO date | Leave blank initially | Canonical effective date | None | Date if populated |
| Last Reviewed | Date | No | Reviewer | ISO date | Leave blank initially | Review audit date | None | Date if populated |
| Created At | Date/time or text | No | Retained.Legacy Created At | Exact observation | Preserve | Legacy creation provenance | None | Optional |
| Updated At | Date/time or text | No | Retained.Legacy Updated At | Exact observation | Preserve | Legacy update provenance | None | Optional |

## Lookup Tables

Lookup sheets contain proposed review values drawn from the canonical workbook,
the retained Repair population, and the protected labor catalog. A
`Legacy Proposed` lookup entry is not an approved canonical identity. Lookup IDs
and service rows require review before any separately authorized import.
