# Competitive Pricing Pilot v0.1 Candidate Report

Status: Proposed ranked cohort; no price recommendation or approval

Date: 2026-07-23

## Source reconciliation

- Pricing source population: 314 records.
- Approved Service Normalization population: 313 records.
- Explicit exclusion: `PRC000268` / `SVC000343`.
- Reconciliation: `314 = 313 eligible + 1 excluded`.
- Proposed pilot: 25 of the 313 eligible records.
- Approved canonical source SHA-256:
  `DE0F0957F687DF4866A2D06C4DF85A542FF58B61897481741EB1E6A04D825FBA`.

`SVC000343` is not present anywhere in the candidate table.

## Evidence limits

- Legacy Retail Price is an observed historical/provisional value, not a recommended
  or final price.
- Related parts evidence comes from the 48-row Master Parts review. Every cited part
  is `Legacy Cost Only` and pending manufacturer review.
- `Component` evidence is stronger than `Consumable`, but neither proves current
  availability, compatibility, quality, or verified supplier cost.
- Demand points are a planning heuristic based on repair category and model
  generation. They are not measured Nocturnix sales demand.
- Canonical mappings are copied exactly from populated source mapping fields. No
  missing mapping was inferred.
- Manufacturer source fields remain `MFR-LEGACY-001` / `N/A`; brand/model scope is
  explicit in Service Name but governed manufacturer/device IDs remain unresolved.

## Ranking rubric

```text
Score =
    4 points: positive Legacy Retail Price
  + 3 points: explicit device/model/operation scope
  + 1–3 points: likely-demand heuristic
  + 0–3 points: related legacy parts evidence
  + 2 points: populated canonical ID/type source mapping
```

Ties are ordered to preserve a balanced mix of screens, batteries, charging ports,
Apple-branded names, Samsung-branded names, and newer/common model cohorts.

## Ranked candidates

| Rank | Score | Pricing Record ID | Service ID | Service Name | Legacy Retail Price | Canonical ID | Canonical Service Type | Scope | Related legacy parts evidence |
| ---: | ---: | --- | --- | --- | ---: | --- | --- | --- | --- |
| 1 | 14 | PRC000202 | SVC000277 | iPhone 7 Battery Replacement | 65 | STY000007 | Battery Replacement | Device-specific and priceable | Component: PRT000037 replacement battery |
| 2 | 14 | PRC000197 | SVC000272 | iPhone X Battery Replacement | 80 | STY000007 | Battery Replacement | Device-specific and priceable | Component: PRT000038 replacement battery |
| 3 | 14 | PRC000229 | SVC000304 | iPhone 7 Charge Port Replacement | 70 | STY000009 | Charging Port Replacement | Device-specific and priceable | Component: PRT000026 charging-port flex |
| 4 | 13 | PRC000057 | SVC000132 | iPhone 12 Screen replacement | 190 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000008 screen adhesive |
| 5 | 13 | PRC000058 | SVC000133 | iPhone 12 Pro Max Screen replacement | 195 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000025 screen adhesive |
| 6 | 13 | PRC000065 | SVC000140 | iPhone 13 Screen replacement | 190 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000022 screen adhesive |
| 7 | 13 | PRC000064 | SVC000139 | iPhone 13 Pro Screen replacement | 200 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000022 screen adhesive |
| 8 | 13 | PRC000070 | SVC000145 | iPhone 14 Plus Screen replacement | 225 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000002 screen adhesive |
| 9 | 13 | PRC000061 | SVC000136 | iPhone 11 Screen replacement | 135 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000024 screen adhesive |
| 10 | 13 | PRC000062 | SVC000137 | iPhone 11 Pro Max Screen replacement | 185 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000024 screen adhesive |
| 11 | 13 | PRC000144 | SVC000219 | iPhone 12 Battery Replacement | 110 | STY000007 | Battery Replacement | Device-specific and priceable | Consumable: PRT000040 battery pulltab |
| 12 | 13 | PRC000146 | SVC000221 | iPhone 12 Pro Battery Replacement | 110 | STY000007 | Battery Replacement | Device-specific and priceable | Consumable: PRT000040 battery pulltab |
| 13 | 12 | PRC000039 | SVC000114 | Galaxy S 10 Screen replacement | 260 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000018 screen adhesive |
| 14 | 12 | PRC000004 | SVC000079 | Galaxy Note 10 Plus Screen replacement | 290 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000014 adhesive pack |
| 15 | 12 | PRC000001 | SVC000076 | Galaxy Note 9 Screen replacement | 225 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000017 screen adhesive |
| 16 | 12 | PRC000122 | SVC000197 | Galaxy Note 10 Plus Battery Replacement | 85 | STY000007 | Battery Replacement | Device-specific and priceable | Consumable: PRT000014 battery adhesive pack |
| 17 | 12 | PRC000130 | SVC000205 | Galaxy S 8 Plus Battery Replacement | 75 | STY000007 | Battery Replacement | Device-specific and priceable | Consumable: PRT000044 battery adhesive |
| 18 | 12 | PRC000126 | SVC000201 | Galaxy S 7 Battery Replacement | 55 | STY000007 | Battery Replacement | Device-specific and priceable | Consumable: PRT000046 battery adhesive |
| 19 | 12 | PRC000173 | SVC000248 | iPhone 8+ Battery Replacement | 70 | STY000007 | Battery Replacement | Device-specific and priceable | Consumable: PRT000045 battery adhesive |
| 20 | 12 | PRC000099 | SVC000174 | iPhone XS Screen replacement | 140 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000011 screen adhesive |
| 21 | 12 | PRC000056 | SVC000131 | iPhone XS Max Screen replacement | 150 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000016 screen adhesive |
| 22 | 12 | PRC000098 | SVC000173 | iPhone XR Screen replacement | 130 | STY000001 | Screen Replacement | Device-specific and priceable | Consumable: PRT000024 screen adhesive |
| 23 | 12 | PRC000238 | SVC000313 | iPhone 11 Charge Port Replacement | 95 | STY000009 | Charging Port Replacement | Device-specific and priceable | No related parts observation |
| 24 | 12 | PRC000242 | SVC000317 | iPhone 12 Charge Port Replacement | 110 | STY000009 | Charging Port Replacement | Device-specific and priceable | No related parts observation |
| 25 | 12 | PRC000246 | SVC000321 | iPhone 13 Charge Port Replacement | 120 | STY000009 | Charging Port Replacement | Device-specific and priceable | No related parts observation |

## Cohort summary

| Measure | Result |
| --- | ---: |
| Candidate records | 25 |
| Positive Legacy Retail Price | 25 |
| Populated source canonical mappings | 25 |
| Device-specific | 25 |
| Device-family-specific | 0 |
| Generic templates | 0 |
| Legacy main-component evidence | 3 |
| Legacy consumable-only evidence | 19 |
| No related parts observation | 3 |
| Screen Replacement | 13 |
| Battery Replacement | 8 |
| Charging Port Replacement | 4 |

## Candidate gates

Selection does not mean price readiness. Before any candidate receives a calculated
recommendation:

1. resolve governed Manufacturer and Device Model IDs;
2. verify main replacement-part compatibility and current supplier cost;
3. verify shipping, consumables, testing, and cost currency/date;
4. approve Labor Standard mapping, minutes, and labor rate;
5. satisfy the competitor-observation minimum under approved market policy;
6. approve overhead, fees, warranty/risk, margin, profit, and rounding policies.

Candidates 23–25 have no related parts observation and should be the first records
paused if component research cannot identify an exact compatible part.
