# Competitive Pricing Pilot v0.1 Workbook Change Plan

Status: Proposed field-by-field plan; no workbook changes authorized

Date: 2026-07-23

## Strategy

Do not add repeated competitor columns to
`Nocturnix_Master_Pricing_Catalog_v1.xlsx`.

The proposed future implementation uses a separate, versioned pilot workbook or
dataset with normalized one-to-many observations. The current Master Pricing V1 file
remains the immutable 314-row source framework.

Proposed pilot artifact:

`D:\Business Portal\300_Pricing\Working\Nocturnix_Competitive_Pricing_Pilot_v0.1.xlsx`

This path is a proposal only. No file has been created.

## Proposed worksheets

| Order | Worksheet | Purpose |
| ---: | --- | --- |
| 1 | `00 - Instructions` | Scope, non-goals, source hashes, and workflow |
| 2 | `01 - Pilot Candidates` | Frozen 25-row candidate cohort and explicit exclusion reconciliation |
| 3 | `02 - Competitor Observations` | One row per competitor offer |
| 4 | `03 - Internal Cost Inputs` | Verified cost and labor evidence per Pricing Record ID |
| 5 | `04 - Pricing Calculations` | Derived cost, market, profitability, and proposed recommendation fields |
| 6 | `05 - Policy Decisions` | Versioned approved values from the policy checklist |
| 7 | `06 - Validation Summary` | Counts, blockers, duplicates, formulas, and approval gates |
| 8 | `07 - Revision History` | Version and decision history |
| 9 | `08 - Import Metadata` | Protected source paths, hashes, versions, and generation metadata |

## `01 - Pilot Candidates`

| Field | Source/action | Rule |
| --- | --- | --- |
| Pilot Rank | Candidate report | Integer 1–25; evidence order only |
| Pilot Score | Candidate report | Integer; store rubric version |
| Pricing Record ID | Master Pricing | Exact copy; unique |
| Service ID | Master Pricing | Exact copy; unique; `SVC000343` prohibited |
| Service Name | Master Pricing | Exact copy |
| Legacy Retail Price | Master Pricing | Reference-only; never final price |
| Canonical Service Type ID | Approved normalization | Copy populated source pair only |
| Canonical Service Type | Approved normalization | Must match canonical ID |
| Scope Classification | Pilot review | Controlled three-value classification |
| Related Parts Evidence | Master Parts review | Reference text/IDs; not verified cost |
| Candidate Status | New | `Proposed`, `Approved for Research`, `Blocked`, `Removed` |
| Blocking Reason | New | Required when blocked/removed |
| Reviewer / Notes | New | Governance evidence |

An exclusion audit row or Validation Summary must record:

`PRC000268 / SVC000343 / Explicit placeholder exclusion`.

## `02 - Competitor Observations`

Use the exact business fields defined in
[COMPETITOR_OBSERVATION_SCHEMA_PROPOSAL.md](COMPETITOR_OBSERVATION_SCHEMA_PROPOSAL.md):

- Observation ID
- Pricing Record ID
- Service ID
- Canonical Service Type ID
- Manufacturer ID / Name
- Device Family ID / Family
- Device Model ID / Model
- Competitor ID / Name / Type
- Regional Market
- Advertised Price
- Mandatory Fees
- Effective Comparison Price
- Currency
- Warranty Term
- Source URL
- Evidence Type
- Observation Date
- Reviewer
- Verification Status
- Notes

`Effective Comparison Price` is a formula:

```excel
=[@[Advertised Price]]+[@[Mandatory Fees]]
```

All aggregate formulas must exclude non-`Verified Comparable` observations.

## `03 - Internal Cost Inputs`

| Field | Current V1 relationship | Planned treatment |
| --- | --- | --- |
| Pricing Record ID | Existing | Exact pilot key |
| Service ID | Existing | Exact relationship |
| Canonical Service Type ID | Missing | Add from approved source pair |
| Verified Part ID | Missing | Add governed compatible part identity |
| Verified Part Cost | Current `Part Cost` blank | Populate only from approved evidence |
| Part Cost Currency | Current `Currency` blank | Required |
| Part Cost Source | Missing | Supplier quote/invoice/catalog reference |
| Part Cost Observation Date | Missing | Required |
| Shipping Cost | Existing blank | Verified allocated amount |
| Consumables | Existing blank | Approved cost method |
| Testing Cost | Existing blank | Approved cost method |
| Labor Standard ID | Existing blank | Approved governed LAB identity |
| Labor Minutes | Current `Standard Labor Minutes` blank | Copy approved Labor Standard value |
| Labor Rate | Existing blank | Approved rate/version |
| Labor Cost | Existing blank | Formula from minutes and rate |
| Overhead Allocation | Existing blank | Approved method/version |
| Processing Fee Flat | Existing single field insufficient | Separate fixed component |
| Processing Fee Rate | Missing | Separate variable component |
| Warranty/Risk Allowance Flat | Existing single fields blank | Separate fixed component |
| Warranty/Risk Allowance Rate | Missing | Separate price-based component if approved |
| Evidence Status | Missing | `Missing`, `Captured`, `Verified`, `Rejected`, `Stale` |
| Reviewer / Verified At | Missing | Required for verified inputs |
| Notes | Existing reviewer notes not input-specific | Cost-specific evidence notes |

Do not map the legacy 265 `NSLC-###` Labor References into governed cost inputs.
They must first reconcile to current `LAB######` identities and approved mappings.

## `04 - Pricing Calculations`

| Field | Existing V1 field | Planned action |
| --- | --- | --- |
| Pricing Record ID | Yes | Retain key |
| Verified Direct Cost | No | Add derived field |
| Labor Cost | Yes, blank | Formula |
| Total Internal Cost | Yes, blank | Formula under policy version |
| Minimum Profit Dollars | No | Add approved policy input/reference |
| Minimum Profitable Price | No | Add formula |
| Target Margin Percent | Yes, blank | Populate by canonical Service Type policy |
| Target-Margin Price | No | Add formula |
| Verified Observation Count | No | Add aggregate QA field |
| Distinct Competitor Count | No | Add aggregate QA field |
| Competitor Low | No | Add filtered aggregate |
| Competitor Median | No | Add filtered aggregate |
| Competitor Average | No | Add filtered aggregate |
| Recommended Price | Yes, blank | Formula/workflow only after method approval |
| Final Approved Price | Current `Final Customer Price` | Human-approved value; never auto-filled |
| Profit Dollars | No | Add formula |
| Gross Margin Percentage | No | Add formula |
| Calculation Status | No | `Blocked`, `Ready for Review`, `Calculated`, `Approved` |
| Policy Version | No | Required provenance |
| Observation Dataset Version | No | Required provenance |
| Cost Dataset Version | No | Required provenance |

Formula definitions are in
[COMPETITIVE_PRICING_PILOT_PLAN.md](COMPETITIVE_PRICING_PILOT_PLAN.md).

## Existing Master Pricing fields

The current 47 fields remain unchanged in the protected V1 workbook.

| Existing field group | Plan |
| --- | --- |
| Pricing Record ID, Service ID, Service Name | Copy into pilot; preserve |
| Legacy Service SKU, Legacy Pricing Status, Legacy Retail Price, Legacy Cost | Reference-only; never overwrite |
| Manufacturer and Device Family fields | Preserve source; add governed pilot IDs when approved |
| Pricing Status, Pricing Method, Review Status, Confidence | Preserve source; pilot has separate lifecycle |
| Part/Shipping/Consumables/Testing fields | Do not populate in protected V1; capture verified values in pilot cost input sheet |
| Labor fields | Do not populate until LAB mapping and rate policies are approved |
| Overhead/fees/warranty/risk | Populate only under approved policy version |
| Total cost, margin, market adjustment, recommended/min/max/final fields | Calculate only in pilot calculation sheet after gates pass |
| Regional Market and dates | Pilot policy-controlled values |
| Source/provenance/reviewer/timestamps | Preserve and extend with dataset/policy versions |

## Validation plan

Before a future pilot workbook can be published:

1. verify protected source hashes before and after;
2. require exact nine-sheet order and one table per worksheet;
3. require 25 unique candidates and one explicit `SVC000343` exclusion;
4. require every canonical pair to match the approved snapshot;
5. reject generic candidates with any recommended/final price;
6. validate all governed ID-name pairs;
7. validate observation formulas and controlled values;
8. scan all formulas for errors and circular references;
9. reconcile observation aggregates to source rows;
10. prove all monetary inputs have currency, source, date, and verification;
11. require policy version on every calculation;
12. require Final Approved Price to be blank until authorized approval;
13. hash and reopen the published artifact;
14. prove no protected workbook changed.

## Rollback and versioning

- Pilot v0.1 is additive and does not migrate Master Pricing.
- Regeneration writes a temporary sibling and publishes atomically only after
  validation.
- A changed candidate list, schema, formula, policy, or source hash requires a new
  pilot version.
- Rejected or superseded observations remain audit history.
- No future pilot workbook becomes a runtime source without a separately approved
  import and activation contract.

