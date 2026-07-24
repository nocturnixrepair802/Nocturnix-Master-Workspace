# Nocturnix Competitive Pricing Pilot v0.1 Plan

Status: Proposed research and design plan; no pricing entry authorized

Date: 2026-07-23

## Purpose

Competitive Pricing Pilot v0.1 defines a controlled first cohort of 25 pricing
records. It is intentionally smaller than the complete catalog and creates no
recommended or final prices.

The pilot is designed to prove that Nocturnix can:

1. select scoped services using documented evidence;
2. preserve canonical Service Type references without inference;
3. capture comparable competitor observations separately from governed prices;
4. assemble verified internal cost inputs;
5. calculate review-ready pricing measures under approved business policies; and
6. retain approval, evidence, and rollback boundaries.

## Protected sources

| Source | Role | Required integrity |
| --- | --- | --- |
| `D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Pricing_Catalog_v1.xlsx` | Primary 314-row pricing review framework | Read-only for Pilot v0.1 planning |
| `D:\Business Portal\300_Pricing\Approved\Nocturnix_Service_Type_Normalization_Approved_v1.0.xlsx` | Canonical Service Type mapping source | SHA-256 `DE0F0957F687DF4866A2D06C4DF85A542FF58B61897481741EB1E6A04D825FBA`; read-only |
| `D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Services_Catalog_v1.xlsx` | Service identity and source context | Read-only |
| `D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Parts_Catalog_v1.xlsx` | Legacy parts/cost evidence only | Read-only; values are not verified supplier costs |

The approved Service Type workbook hash was verified before analysis. No source
workbook was saved or modified.

## Population reconciliation

The population gate is:

```text
314 legacy Master Pricing records
- 1 explicit placeholder exclusion (SVC000343 / PRC000268)
= 313 eligible records present in approved Service Normalization
```

Rules:

- `SVC000343` is excluded from candidate selection, competitor observations,
  cost research, calculations, recommendations, approval, and future pilot output.
- Its absence is reconciled as an explicit exclusion, never as a dropped row.
- Every selected Service ID must resolve to exactly one Pricing Record ID and one
  populated source canonical ID/type pair.
- A missing canonical pair blocks candidate selection. Pilot v0.1 does not infer it.

## Pilot cohort

The proposed cohort contains 25 device-specific records:

- 13 Screen Replacement records;
- 8 Battery Replacement records; and
- 4 Charging Port Replacement records.

All 25 have:

- a positive Legacy Retail Price observation;
- a complete device/model-specific Service Name;
- a populated source mapping to `STY000001`, `STY000007`, or `STY000009`;
- a high or medium demand heuristic; and
- either related legacy parts evidence or an explicit parts-research gap.

The ranked cohort and evidence limits are in
[COMPETITIVE_PRICING_PILOT_CANDIDATES.md](COMPETITIVE_PRICING_PILOT_CANDIDATES.md).

## Scope classification

Each proposed candidate must receive exactly one classification:

| Classification | Rule | Pricing treatment |
| --- | --- | --- |
| Device-specific and priceable | Service Name identifies manufacturer brand, device model, and operation | Eligible for cost and competitor research; not automatically eligible for final pricing |
| Device-family-specific and potentially priceable | Family is clear but no exact model is established | Research may begin at family level, but device applicability and price comparability must be approved |
| Generic service template requiring further device scope | Neither an exact device nor an approved family scope is present | No recommended or final price |

All 25 proposed Pilot v0.1 candidates are classified
`Device-specific and priceable` from their explicit Service Names. However, the
source Manufacturer fields remain `MFR-LEGACY-001` / `N/A`; brand/model tokens in
Service Name do not repair those governed identifiers. Manufacturer and Device Model
IDs must be resolved before activation or final approval.

No generic template is included. If a generic template is added later, all calculated
and final price fields must remain blank.

## Ranking method

The ranking is evidence-based, not a price recommendation.

| Factor | Points | Rule |
| --- | ---: | --- |
| Positive Legacy Retail Price | 4 | Positive numeric observation; remains legacy/unverified |
| Clear device-specific scope | 3 | Brand, model, and operation present in Service Name |
| Likely demand | 1–3 | Screen, battery, and charge-port services; recent/common models rank above aging models |
| Related parts evidence | 0–3 | 3 for a legacy main-component observation; 1 for consumable/adhesive evidence; 0 for none |
| Populated canonical mapping | 2 | Exact source ID/type pair; no inferred mapping |

Maximum score: 15.

Demand is a planning heuristic only. It is not supported by Nocturnix sales-volume
data in the current workbook and must not be presented as measured demand.

Related parts evidence is also limited:

- `Component` means a related legacy component record exists.
- `Consumable` means only adhesive, pulltab, or similar supporting material exists.
- neither class proves current availability, compatibility, quality, or verified
  supplier cost;
- every related part remains `Legacy Cost Only` and pending manufacturer review.

## Pilot phases and gates

### Gate 0 — Source freeze and candidate approval

- Reverify both source hashes.
- Approve the 25-row candidate list and explicit `SVC000343` exclusion.
- Confirm canonical ID/type pairs against the approved workbook.
- Confirm that no generic templates are included.

Exit criterion: candidate report signed by pricing governance and catalog owner.

### Gate 1 — Identity and scope resolution

- Assign governed Manufacturer ID and Device Model ID for each candidate.
- Confirm that each advertised competitor service is comparable to the selected
  Nocturnix service scope.
- Resolve naming anomalies without changing the legacy source.

Exit criterion: every candidate has approved device/manufacturer scope.

### Gate 2 — Internal cost evidence

- Obtain verified part, shipping, consumable, and testing costs.
- Map an approved Labor Standard and labor minutes.
- Approve labor rate, overhead, processing-fee, and warranty/risk policies.
- Record source, observation date, currency, reviewer, and verification state for
  every cost input.

Exit criterion: every calculation input is either verified or explicitly blocked.

### Gate 3 — Competitor observations

- Create the separate observation dataset defined in
  [COMPETITOR_OBSERVATION_SCHEMA_PROPOSAL.md](COMPETITOR_OBSERVATION_SCHEMA_PROPOSAL.md).
- Collect no prices until competitor categories, market, currency, comparison rules,
  and evidence requirements are approved.
- Reject observations that do not match service, device, geography, currency, or
  mandatory-fee comparison rules.

Exit criterion: the minimum approved count and mix of verified comparable observations
per candidate is met.

### Gate 4 — Calculation review

- Calculate internal cost and profitability measures.
- Calculate competitor low, median, and average from verified comparable observations.
- Apply the approved pricing method and rounding policy to a proposed recommended
  price.
- Keep Final Approved Price blank.

Exit criterion: calculation validator passes and no blocked candidate has a
recommendation.

### Gate 5 — Final approval

- An authorized reviewer records Final Approved Price and effective dates.
- Approval evidence identifies policy version, source dataset version, calculator
  version, reviewer, and timestamp.
- Production activation remains a separate future process.

## Calculation contract

The formulas below are proposed. They are inactive until the policy checklist is
approved.

### Base inputs

All monetary inputs must share an approved currency and effective market:

```text
Verified Direct Cost =
    Verified Part Cost
  + Shipping Cost
  + Consumables
  + Testing Cost

Labor Cost = (Labor Minutes / 60) * Labor Rate
```

### Internal cost

If processing fees and warranty/risk allowance are fixed amounts:

```text
Total Internal Cost =
    Verified Direct Cost
  + Labor Cost
  + Overhead Allocation
  + Processing Fees
  + Warranty/Risk Allowance
```

If a fee or allowance is price-based, it must not be inserted into this simple sum.
The price equation must solve for the variable percentage explicitly to avoid a
circular formula.

### Profit thresholds

For fixed costs:

```text
Minimum Profitable Price =
    Total Internal Cost + Minimum Profit Dollars

Target-Margin Price =
    Total Internal Cost / (1 - Target Gross Margin Percentage)
```

For price-based processing/risk rates:

```text
Minimum Profitable Price =
    (Fixed Internal Cost + Flat Fees + Minimum Profit Dollars)
    / (1 - Processing Fee Rate - Price-Based Risk Rate)

Target-Margin Price =
    (Fixed Internal Cost + Flat Fees)
    / (1 - Processing Fee Rate - Price-Based Risk Rate
         - Target Gross Margin Percentage)
```

The denominator must be greater than zero. Invalid or missing policy values block the
calculation.

### Competitor statistics

For the same Pricing Record ID, device scope, approved market, currency, comparison
date window, and verification state:

```text
Effective Comparison Price = Advertised Price + Mandatory Fees
Competitor Low = MIN(verified effective comparison prices)
Competitor Median = MEDIAN(verified effective comparison prices)
Competitor Average = AVERAGE(verified effective comparison prices)
```

Duplicate observations, stale observations, noncomparable warranties/scopes, and
unverified evidence are excluded from the aggregate.

### Recommendation and approval

`Recommended Price` is a governed output, not simply the competitor median. Its
approved method must consider at least:

- Minimum Profitable Price;
- Target-Margin Price;
- competitor low/median/average;
- documented service value or risk adjustments; and
- the approved rounding convention.

No formula is approved for Recommended Price in v0.1. The decision checklist must
select and version a method first.

```text
Final Approved Price = authorized human approval of a reviewed recommendation
Profit Dollars = Final Approved Price - Total Internal Cost
Gross Margin Percentage = Profit Dollars / Final Approved Price
```

Final Approved Price of zero or blank produces no gross-margin result.

## Required governance

The unresolved decisions are tracked in
[PRICING_POLICY_DECISION_CHECKLIST.md](PRICING_POLICY_DECISION_CHECKLIST.md).
Until every blocking decision is approved:

- competitor observations may not be collected;
- internal-cost fields may not be labeled verified;
- recommended and final prices remain blank;
- no price may affect runtime or production data.

## Workbook implementation boundary

The proposed future workbook changes are defined field-by-field in
[COMPETITIVE_PRICING_WORKBOOK_CHANGE_PLAN.md](COMPETITIVE_PRICING_WORKBOOK_CHANGE_PLAN.md).

Pilot planning creates documentation only. It does not authorize:

- editing either protected workbook;
- generating a replacement pricing workbook;
- entering competitor or cost values;
- calculating or approving prices;
- changing canonical Service Type data;
- changing runtime pricing behavior.

## Pilot acceptance criteria

Pilot v0.1 design is ready for governance review when:

- the population equation is exactly `314 = 313 + 1`;
- `SVC000343` appears only in the exclusion record;
- exactly 25 ranked candidates resolve to approved source mappings;
- every candidate has one scope classification;
- the observation schema is complete and separated from pricing records;
- all calculation fields have definition, unit, source, and blocking behavior;
- the policy checklist names an owner and approval evidence for every decision;
- the workbook change plan is additive, versioned, and reversible;
- no source workbook or production path changed.
