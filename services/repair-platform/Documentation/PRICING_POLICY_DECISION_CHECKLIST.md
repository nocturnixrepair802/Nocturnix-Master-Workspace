# Competitive Pricing Pilot v0.1 Policy Decision Checklist

Status: Open governance checklist; all blocking items require explicit approval

Date: 2026-07-23

## Approval record requirements

Every decision requires:

- selected policy and rejected alternatives;
- accountable business owner;
- data/technical reviewer where applicable;
- approval date;
- effective date;
- policy version;
- affected Service Types or records;
- test and rollback requirements.

No unchecked blocking item may be replaced with a developer default.

## Blocking business-policy decisions

### Currency

- [ ] Approve the pilot transaction and observation currency.
- [ ] Decide whether non-pilot-currency observations are rejected or converted.
- [ ] If converted, approve exchange-rate source, rate date, precision, and retained
  original amount/currency.
- [ ] Decide whether taxes are included or excluded from comparison.

Owner: Pricing governance  
Blocking: Yes

### Primary regional market

- [ ] Define the pilot geography precisely: city/metro, radius, postal codes, or
  service area.
- [ ] Define treatment of mobile, mail-in, and online-only competitors.
- [ ] Define whether competitor locations outside the market may be used.
- [ ] Approve the market label stored in each observation.

Owner: Business/pricing owner  
Blocking: Yes

### Competitor categories

- [ ] Approve controlled Competitor Type values.
- [ ] Decide which categories are comparable for each Service Type.
- [ ] Decide whether OEM/authorized, independent, mobile, and mail-in offers may be
  pooled or must be segmented.
- [ ] Define competitor identity/location deduplication.

Owner: Pricing governance  
Blocking: Yes

### Observation sufficiency and freshness

- [ ] Set minimum verified observations per Pricing Record ID.
- [ ] Set minimum distinct competitors.
- [ ] Set observation-age/staleness threshold.
- [ ] Define required evidence by Evidence Type.
- [ ] Define treatment of appointments, memberships, coupons, taxes, and conditional
  discounts.
- [ ] Define comparability rules for part quality and warranty differences.

Owner: Pricing governance and compliance  
Blocking: Yes

### Labor rate

- [ ] Approve Labor Standard ID mapping source and row-status gate.
- [ ] Approve labor-rate basis: technician wage burden, shop rate, or another model.
- [ ] Approve one rate or tiered rates by skill/difficulty.
- [ ] Approve units, precision, minimum billable increment, and rounding.
- [ ] Approve handling of rework, calibration, programming, and testing time.

Owner: Labor standards and finance  
Blocking: Yes

### Processing-fee formula

- [ ] Approve fee components: flat, percentage, or blended.
- [ ] Decide whether fees are applied to subtotal, customer price, or payment-method
  amount.
- [ ] Approve whether the fee is absorbed or passed through.
- [ ] Approve formula treatment that avoids circular calculations.
- [ ] Approve payment-method assumptions and rate source.

Owner: Finance  
Blocking: Yes

### Overhead allocation

- [ ] Approve overhead pool and included expense categories.
- [ ] Approve allocation driver: labor hours, jobs, revenue, direct cost, or another
  basis.
- [ ] Approve allocation period and refresh schedule.
- [ ] Approve Service Type or location differences.
- [ ] Approve minimum/maximum allocation if applicable.

Owner: Finance  
Blocking: Yes

### Warranty/risk allowance

- [ ] Approve included risks: warranty returns, breakage, diagnostics, part defects,
  water resistance, calibration, and rework.
- [ ] Approve fixed versus percentage method.
- [ ] Approve Service Type/device risk tiers.
- [ ] Approve evidence and review frequency.
- [ ] Approve interaction with warranty term in competitor comparison.

Owner: Operations and finance  
Blocking: Yes

### Target margin by Service Type

- [ ] Approve gross-margin definition and denominator.
- [ ] Set target margin for `STY000001` Screen Replacement.
- [ ] Set target margin for `STY000007` Battery Replacement.
- [ ] Set target margin for `STY000009` Charging Port Replacement.
- [ ] Define exception approval and floor behavior.
- [ ] Define whether target margin differs by device age, part quality, or risk.

Owner: Pricing owner and finance  
Blocking: Yes

### Price rounding convention

- [ ] Approve rounding precision.
- [ ] Approve permitted endings, if any.
- [ ] Decide whether minimum profitable price rounds upward only.
- [ ] Approve sequence: calculate, apply floor, round, then revalidate margin.
- [ ] Define exception handling when rounding violates minimum profit.

Owner: Pricing owner  
Blocking: Yes

### Minimum profit threshold

- [ ] Approve minimum profit dollars per repair.
- [ ] Decide whether a minimum gross-margin percentage also applies.
- [ ] Define Service Type/device exceptions.
- [ ] Define escalation for records below threshold.
- [ ] Define whether diagnostic or strategic services may use a different threshold.

Owner: Finance and business owner  
Blocking: Yes

## Additional required decisions

### Cost evidence

- [ ] Define `Verified Part Cost`.
- [ ] Approve supplier identity and quote/invoice evidence.
- [ ] Define shipping allocation across multi-item orders.
- [ ] Define consumables and testing-cost methods.
- [ ] Define cost-currency conversion and observation-age thresholds.
- [ ] Define approved part-quality/OEM tiers.

### Recommendation method

- [ ] Choose the method relating Minimum Profitable Price, Target-Margin Price, and
  competitor aggregates.
- [ ] Define permissible market adjustment.
- [ ] Define behavior when competitor observations are insufficient.
- [ ] Define behavior when the market median is below the profitable floor.
- [ ] Define reviewer authority and exception evidence.

### Final approval and publication

- [ ] Name the Final Approved Price authority.
- [ ] Define effective/expiration-date rules.
- [ ] Define dual-control or second-review requirements.
- [ ] Define publication/activation process and rollback.
- [ ] Define monitoring triggers for cost or market changes.

## Pilot readiness decision

The checklist is ready to proceed only when all ten blocking policy areas are
approved:

1. Currency
2. Primary regional market
3. Competitor categories
4. Observation sufficiency/freshness
5. Labor rate
6. Processing-fee formula
7. Overhead allocation
8. Warranty/risk allowance
9. Target margin by Service Type
10. Price rounding and minimum-profit thresholds

Until then, the pilot may refine schemas and candidate evidence but may not collect
competitor prices or calculate recommendations.

