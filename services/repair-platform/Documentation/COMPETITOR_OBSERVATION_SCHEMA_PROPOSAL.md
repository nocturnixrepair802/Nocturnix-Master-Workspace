# Competitor Observation Schema Proposal

Status: Proposed for Competitive Pricing Pilot v0.1; no observations collected

Date: 2026-07-23

## Purpose

Competitor observations are time-sensitive market evidence. They must be stored
separately from Master Pricing records so multiple observations can support one
Pricing Record ID without adding repeated competitor columns or overwriting history.

The proposed dataset is append-only by version. Corrections supersede an observation;
they do not silently edit evidence used by a prior pricing decision.

## Proposed identity

- Dataset name:
  `Nocturnix_Competitive_Pricing_Observations_v0.1`
- Proposed Observation ID format: `CPO######`
- Proposed natural duplicate key:
  `(Pricing Record ID, Competitor ID, Source URL, Observation Date,
  Advertised Price, Mandatory Fees)`
- One observation describes one competitor offer for one comparable service scope.

Observation ID authority and sequence require explicit governance approval.

## Field definitions

| Field | Type | Required | Rule |
| --- | --- | ---: | --- |
| Observation ID | Text | Yes | Proposed `^CPO\d{6}$`; unique and immutable |
| Pricing Record ID | Text | Yes | Must resolve to the approved Pilot v0.1 candidate set; `SVC000343` lineage prohibited |
| Service ID | Text | Yes | Must equal the Service ID belonging to Pricing Record ID |
| Canonical Service Type ID | Text | Yes | Copy populated pilot mapping; must resolve to the approved canonical snapshot |
| Manufacturer ID | Text | Yes | Governed ID; legacy placeholder prohibited for verified observations |
| Manufacturer Name | Text | Yes | Must match Manufacturer ID |
| Device Family ID | Text | Yes | Governed family identifier |
| Device Family | Text | Yes | Must match Device Family ID |
| Device Model ID | Text | Yes for device-specific | Governed model identifier; blank only under an approved family-scope rule |
| Device Model | Text | Yes for device-specific | Must match Device Model ID |
| Competitor ID | Text | Yes | Governed competitor/business-location identity |
| Competitor Name | Text | Yes | Must match Competitor ID |
| Competitor Type | Controlled text | Yes | Must use approved categories |
| Regional Market | Controlled text | Yes | Must use the approved pilot market |
| Advertised Price | Decimal | Yes | Nonnegative monetary amount; no currency symbols stored in value |
| Mandatory Fees | Decimal | Yes | Nonnegative; use zero only when verified that no mandatory fees apply |
| Effective Comparison Price | Decimal/formula | Yes | `Advertised Price + Mandatory Fees`; never manually keyed |
| Currency | ISO text | Yes | Approved ISO 4217 code, expected pilot value pending decision |
| Warranty Term | Structured text | Yes | Comparable term or explicit `None`; definition must be standardized |
| Source URL | URL text | Yes | Direct evidence page where available; URL must pass validation |
| Evidence Type | Controlled text | Yes | Approved evidence category |
| Observation Date | Date | Yes | Date the price was actually observed, not file creation date |
| Reviewer | Text | Yes for verified | Accountable reviewer identity |
| Verification Status | Controlled text | Yes | Lifecycle below |
| Notes | Text | No | Scope exceptions, tax treatment, appointment requirements, exclusions, or evidence limits |

## Proposed controlled values

### Verification Status

- `Captured`
- `Pending Verification`
- `Verified Comparable`
- `Verified Noncomparable`
- `Stale`
- `Rejected`
- `Superseded`

Only `Verified Comparable` observations may enter competitor aggregates.

### Evidence Type

- `Competitor Website`
- `Online Booking Quote`
- `Written Estimate`
- `Published Price List`
- `In-Store Verified`
- `Phone Verified`

The policy owner must decide which types are sufficient for verified use and what
supporting artifact is required.

### Competitor Type

Proposed categories for decision, not yet approved:

- `OEM / Authorized Service`
- `National Repair Chain`
- `Regional Repair Chain`
- `Independent Local Repair Shop`
- `Mobile Repair Provider`
- `Mail-In Repair Provider`
- `Marketplace / Informal Provider`

## Validation rules

1. Pricing Record ID, Service ID, canonical pair, and device scope must agree.
2. `SVC000343` is prohibited.
3. Effective Comparison Price must equal Advertised Price plus Mandatory Fees.
4. Currency and market must be approved and nonblank.
5. Source URL, evidence type, and observation date are required for verification.
6. Future observation dates fail validation.
7. Observation age is calculated from Observation Date; stale thresholds are policy.
8. Duplicate natural keys fail or route to duplicate review.
9. Manufacturer/Family/Model ID-name pairs must resolve to governed references.
10. A device-specific pricing record cannot use a family-only observation unless an
    explicit comparability decision documents why.
11. Warranty, diagnostic fee, membership requirement, part quality, and tax inclusion
    differences must be recorded before an observation can be comparable.
12. Rejected, stale, noncomparable, and superseded rows remain audit evidence but do
    not enter low/median/average calculations.

## Aggregation contract

Competitor aggregates group only observations sharing:

- Pricing Record ID and Service ID;
- canonical Service Type;
- governed manufacturer/family/model scope;
- approved Regional Market;
- Currency;
- approved observation-age window;
- `Verified Comparable` state.

Required result fields:

- observation count;
- distinct competitor count;
- oldest and newest observation date;
- Competitor Low;
- Competitor Median;
- Competitor Average;
- excluded observation count and reasons.

The required minimum observation and distinct-competitor counts remain policy
decisions. When the minimum is not met, aggregate values may be displayed for review
but Recommended Price remains blocked.

## Audit and provenance fields for implementation

The user-requested dataset fields are the business schema. A future implementation
should additionally persist:

- observation dataset version;
- source workbook/file hash;
- captured timestamp;
- verified timestamp;
- superseded observation ID;
- created/updated actor;
- row digest;
- evidence artifact reference or retained screenshot/document hash where permitted.

These technical provenance fields must not replace the business fields above.

## Non-goals

Pilot v0.1 does not:

- collect competitor observations;
- scrape websites;
- invent missing prices or fees;
- convert legacy prices into competitor observations;
- calculate a recommendation;
- modify the Master Pricing workbook.

