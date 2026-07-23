# ADR-007: Master Pricing Identity and Schema

- Status: Accepted
- Date: 2026-07-23

## Context

The canonical workbook worksheet `50 Pricing` contains legacy labor, parts, and
retail pricing examples, but it has no `Pricing Record ID` column and no
canonical pricing-record identifiers. Existing `RULE########` values identify
pricing rules. They are not pricing records and must not be reused as pricing
record identities.

The proposed Master Pricing schema also needs to preserve the pricing-review
status copied from Master Services while maintaining a separate governed Master
Pricing lifecycle. One field cannot represent both meanings safely.

## Decision

- Establish `PRC######` as the canonical Pricing Record ID format.
- Require prefix `PRC`, exactly six numeric digits, and regex
  `^PRC\d{6}$`.
- Treat the current namespace as an approved empty namespace whose first
  allocation is `PRC000001`.
- For the current 314-record review population, expect `PRC000001` through
  `PRC000314`.
- When valid canonical PRC IDs later exist, allocate after the highest valid
  identifier.
- Pricing Record IDs are immutable, unique, and never reused or renumbered.
- Report malformed identifiers and exclude them from sequence calculation.
- Reject duplicate valid canonical identifiers.
- Accept the 47-column Master Pricing schema.
- Preserve `Legacy Pricing Status` as the Master Services source observation.
- Use `Pricing Status` only for the governed Master Pricing lifecycle.
- Never overwrite or substitute either status field for the other.
- Assigning a Pricing Record ID does not approve a price, pricing method,
  calculation, publication, or canonical import.

## Consequences

- The generator may allocate from `PRC000001` when `50 Pricing` has no Pricing
  Record ID column or contains no valid PRC IDs. This is an approved namespace
  rule, not a guessed default.
- Future generation continues dynamically after the highest valid canonical PRC
  ID without changing existing identifiers.
- Initial pricing records remain draft review records with blank calculated and
  final customer-price fields.
- Canonical import and customer-price approval remain separate, explicitly
  authorized processes.
- Currency, cost, margin, regional-market, calculation, rounding, approval,
  effective-date, and publication policies remain unresolved.

## References

- `Documentation/MASTER_PRICING_SPEC.md`
- `Documentation/MASTER_PRICING_DATA_DICTIONARY.md`
- `Documentation/MASTER_PRICING_VALIDATION_RULES.md`
- `Documentation/ADR/ADR-005-decimal-for-money.md`
- `Documentation/ADR/ADR-006-canonical-master-catalog-baseline.md`
