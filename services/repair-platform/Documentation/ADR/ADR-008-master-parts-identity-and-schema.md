# ADR-008: Master Parts Identity and Schema

- Status: Accepted
- Date: 2026-07-23

## Context

The legacy catalog mixes part identity, inventory observations, supplier
observations, and provisional monetary values. A Legacy SKU may repeat, and
supplier, condition, stock, serial number, and bin values can vary without
creating a different physical part identity.

Read-only inspection found an empty `Part ID` column in canonical worksheet
`39.4 Repair Parts`. Worksheet `41 Parts` contains a legacy `SKU` column but no
canonical Part ID column. Neither worksheet contains a valid `PRT######` value.

## Decision

- Master Parts is a catalog of part identities and sourcing references. It is
  separate from inventory, stock-on-hand, purchasing, and final pricing.
- Approve `PRT######` as the canonical Part ID format, with prefix `PRT`,
  exactly six digits, and regex `^PRT\d{6}$`.
- Treat the current namespace as an approved empty namespace beginning at
  `PRT000001`.
- When valid canonical Part IDs later exist, continue after the highest valid
  identifier.
- Part IDs are immutable, unique, and never reused or renumbered.
- Reject duplicate valid existing IDs. Report malformed IDs and exclude them
  from sequence calculation.
- Legacy SKU is an alias/reference only and is never the canonical primary key.
- Supplier and cost values copied from legacy sources remain provisional
  observations.
- Multiple suppliers belong in a sourcing relationship or supplier-cost
  structure. Supplier differences do not automatically duplicate part identity.
- Inventory quantity, serial number, condition, bin, and location do not define
  canonical part identity.
- Compatibility is a separately reviewed relationship and is not inferred
  merely to complete a part record.
- Canonical import requires separate authorization.

## Accepted Schema

Accept the 50-column Master Parts schema documented in
`MASTER_PARTS_DATA_DICTIONARY.md`. The schema preserves legacy observations,
keeps compatibility and sourcing unresolved when evidence is insufficient, and
does not contain calculated landed cost or final customer pricing.

## Consequences

- The current 48-row review population is expected to receive `PRT000001`
  through `PRT000048`.
- Assigning a proposed Part ID does not approve identity, supplier, cost,
  compatibility, inventory, pricing, or canonical import.
- Initial records remain Draft and pending review.
- Future multi-supplier and compatibility structures require separately approved
  relationship schemas.

## References

- `Documentation/MASTER_PARTS_SPEC.md`
- `Documentation/MASTER_PARTS_DATA_DICTIONARY.md`
- `Documentation/MASTER_PARTS_VALIDATION_RULES.md`
- `Documentation/ADR/ADR-006-canonical-master-catalog-baseline.md`
