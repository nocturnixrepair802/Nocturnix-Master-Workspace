# Master Pricing Catalog V1 Data Dictionary

ADR-007 approves the primary `tblMasterPricingCatalog` schema with 47 fields.
Required means
required in generated V1 unless a rule explicitly requires the field to remain
blank. Source monetary values are observations, not approved inputs.

| Field | Type | Req. | Source | Valid values / transformation | Business meaning and validation | Blank / zero behavior |
|---|---|---:|---|---|---|---|
| Pricing Record ID | Text | Yes | ADR-007 and canonical `50 Pricing` | `PRC000001` for an empty namespace; otherwise next `PRC######` after the highest valid existing ID | Draft pricing-record identity; unique, continuous, immutable, never reused; does not approve pricing | Blank prohibited |
| Service ID | Text | Yes | Master Services | Copy `SVC######` | Required service relationship; unique and source ordered | Blank prohibited |
| Legacy Service SKU | Text | No | Master Services | Copy only | Legacy alias/reference | Blank preserved |
| Service Name | Text | Yes | Master Services | Copy only | Review label; must equal service source | Blank prohibited |
| Manufacturer ID | Text | Conditional | Master Services | Copy only | Must pair with source Manufacturer Name | Blank preserved |
| Manufacturer Name | Text | Conditional | Master Services | Copy only | Human relationship label | Blank preserved |
| Device Family Code | Text | Conditional | Master Services | Copy only | Must pair with source Device Family Name | Blank preserved |
| Device Family Name | Text | Conditional | Master Services | Copy only | Human relationship label | Blank preserved |
| Legacy Pricing Status | Text | Yes | Master Services.Pricing Status | Copy only | Preserves upstream pricing-review state | Blank prohibited |
| Pricing Status | Text | Yes | V1 rule | Controlled lifecycle | Derived by labor, cost, then market readiness | Blank prohibited |
| Pricing Method | Text | Yes | V1 rule | Controlled; default `Not Yet Determined` | Proposed calculation method | Never inferred from legacy price |
| Currency | Text | No | Future confirmation | Controlled currency code | Monetary denomination | Blank unresolved; no USD default |
| Legacy Retail Price | Decimal/text | No | Master Services | Copy only | Historical/provisional observation | Zero preserved; blank distinct; invalid text preserved |
| Legacy Cost | Decimal/text | No | Master Services | Copy only | Historical/provisional observation | Zero is not verified cost; blank distinct |
| Part Cost | Decimal | No | Future evidence | Nonnegative | Verified parts input | Blank unresolved; zero requires evidence |
| Shipping Cost | Decimal | No | Future evidence | Nonnegative | Verified shipping input | Blank unresolved |
| Consumables Cost | Decimal | No | Future evidence | Nonnegative | Verified consumables input | Blank unresolved |
| Testing Cost | Decimal | No | Future evidence | Nonnegative | Verified testing/diagnostic input | Blank unresolved |
| Labor Standard ID | Text | No | Master Services | Copy only; valid labor ID | Labor-standard relationship | Blank routes to Labor Mapping Required |
| Standard Labor Minutes | Integer | No | Labor catalog | Copy referenced Standard Minutes | Labor duration reference, not price | Blank with no labor mapping |
| Labor Rate Tier | Text | No | Labor catalog | Copy referenced tier | Rate-tier relationship | Blank with no labor mapping |
| Labor Rate | Decimal | No | Future approved rate | Nonnegative | Verified rate input | Blank unresolved; never inferred |
| Labor Cost | Decimal | No | Future approved model | Nonnegative | Calculated/verified labor cost | Always blank in generated V1 |
| Overhead Allocation | Decimal | No | Future policy | Nonnegative | Approved overhead input | Blank unresolved |
| Processing Fees | Decimal | No | Future policy | Nonnegative | Approved fee input | Blank unresolved |
| Warranty Allowance | Decimal | No | Future policy | Nonnegative | Approved warranty exposure | Blank unresolved |
| Risk Allowance | Decimal | No | Future policy | Nonnegative | Approved repair-risk input | Blank unresolved |
| Total Internal Cost | Decimal | No | Future approved model | Nonnegative | Sum under approved model | Blank if any required cost is unresolved |
| Target Margin Percent | Decimal | No | Margin Targets | 0 through 1 | Approved target margin | Blank unresolved; zero is a target only if approved |
| Market Adjustment | Decimal | No | Future policy | Documented approved range | Regional adjustment | Blank unresolved |
| Recommended Price | Decimal | No | Future approved model | Nonnegative | Candidate review price | Always blank in V1 |
| Minimum Approved Price | Decimal | No | Future approval | Nonnegative | Approved floor | Always blank in generated V1 |
| Maximum Approved Price | Decimal | No | Future approval | Nonnegative | Approved ceiling | Always blank in generated V1 |
| Final Customer Price | Decimal | No | Future approval | Nonnegative | Publishable price | Always blank in V1 |
| Regional Market | Text | No | Regional Markets | Controlled approved region | Market context | Blank unresolved |
| Effective Date | Date | No | Future approval | Excel date | Pricing effective date | Blank in generated V1 |
| Expiration Date | Date | No | Future approval | Excel date; not before effective date | Pricing expiration | Blank in generated V1 |
| Review Status | Text | Yes | V1 rule/reviewer | Controlled; default `Pending Review` | Review workflow | Blank prohibited; no preapproval |
| Pricing Confidence | Text | Yes | V1 rule/reviewer | Unassessed, Low, Medium, High | Evidence confidence | Default `Unassessed` |
| Source Record Number | Integer | Yes | Master Services | Copy only | Legacy provenance | Positive and unique |
| Source Workbook | Text | Yes | Master Services | Copy only | Original retained source | Blank prohibited |
| Source Worksheet | Text | Yes | Master Services | Copy only | Original retained worksheet | Blank prohibited |
| Import Batch ID | Text | Yes | Generator | `MASTER-PRICING-V1-REVIEW` | Generation batch | Blank prohibited |
| Reviewer | Text | No | Reviewer | ASCII-safe text | Review owner | Blank pending |
| Reviewer Notes | Text | No | Reviewer | ASCII-safe text | Review evidence | Blank pending |
| Created At | Date/time or text | No | Master Services | Copy only | Legacy creation provenance | Blank preserved |
| Updated At | Date/time or text | No | Master Services | Copy only | Legacy update provenance | Blank preserved |

## Controlled Values

Pricing Status:

- Pending Pricing Review
- Legacy Price Review
- Cost Research Required
- Labor Mapping Required
- Market Research Required
- Ready for Pricing Calculation
- Ready for Approval
- Approved
- Rejected
- Archived

Pricing Method:

- Cost Plus
- Market Aligned
- Fixed Service Fee
- Diagnostic Fee
- Labor Only
- Parts and Labor
- Manual Review
- Not Yet Determined

Review Status:

- Pending Review
- In Review
- Ready for Approval
- Approved
- Rejected
- Archived

Pricing Confidence:

- Unassessed
- Low
- Medium
- High

`USD` is the sole candidate currency in V1 lookup data, but generated rows
remain blank until source or business configuration confirms currency.

## Cost Component Governance

Required research components are Part Cost, Shipping Cost, Consumables Cost,
Testing Cost, Labor Rate, Labor Cost, Overhead Allocation, Processing Fees,
Warranty Allowance, and Risk Allowance. The generated V1 rows leave all of them
blank. A populated zero is accepted only as an evidenced zero, not as a
substitute for missing data.

## Lookup Ownership

- Service references and legacy observations: Master Services.
- Labor ID, minutes, and tier: protected Labor Standards.
- Pricing statuses, methods, review statuses, confidence: Master Pricing V1.
- Margin targets, regional markets, rate values, and currency confirmation:
  pending owner approval.

The approved identity and schema contract is defined by
`Documentation/ADR/ADR-007-master-pricing-identity-and-schema.md`. Initial rows
remain draft review records. Final Customer Price is blank and unapproved.
