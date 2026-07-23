# ADR-010: Master Compatibility Relationship Governance

- Status: Accepted
- Date: 2026-07-23

## Context

Compatibility is currently represented in canonical worksheet
`35 Compatibility Matrix`. Its relationship fields are legacy-shaped: the
field labelled `Service Name` contains Service IDs and the rows describe
family-to-service support. The platform now needs a review package that can
represent service and part relationships at family, model, and variant
granularity without changing any catalog identity or protected workbook.

Read-only inspection on 2026-07-23 found a `Compatibility ID` header on row 2
of `35 Compatibility Matrix`. The sheet contains 82 valid, unique, continuous
IDs from `CMP000001` through `CMP000082`. No duplicate or malformed populated
IDs were found.

## Decision

- Compatibility is a governed relationship, not a device, service, or part
  catalog identity.
- Device-to-Service and Device-to-Part are separate relationship types.
- Family-level, model-level, and variant-level relationships are distinct and
  may not be substituted for one another.
- Every proposed relationship preserves its evidence type, evidence source,
  evidence detail, provenance, and review requirement.
- Inferred relationships remain Proposed and inactive until reviewed.
- Unsupported relationships are not created. Weak name similarity,
  manufacturer-only agreement, and generic product words are insufficient.
- Generators and validators inspect existing canonical Compatibility IDs at
  runtime. Duplicate valid IDs are rejected. Malformed populated IDs are
  reported separately and excluded from sequence arithmetic.
- Canonical Compatibility IDs are immutable, unique, never reused, and never
  renumbered.
- The canonical format is `CMP` followed by six digits, with regex
  `^CMP\d{6}$`.
- When valid IDs exist, allocation continues after the highest valid ID. When
  the canonical `Compatibility ID` column is structurally valid but empty,
  this ADR authorizes the namespace to begin at `CMP000001`.
- IDs are allocated deterministically by Relationship Type, Device ID,
  Service ID or Part ID, and Source Record Number. Family code is used only as
  a deterministic tie-breaker when Device ID is intentionally blank.
- A proposed ID identifies a review record only. Canonical import requires a
  separate authorized migration, backup, validation, approval, and rollback
  plan.
- Relationship approval does not approve price, cost, stock, inventory
  availability, purchasing, or fulfillment.

## Consequences

- With the inspected canonical state, the expected first generated ID is
  `CMP000083`.
- Generated relationships cannot be Confirmed or Approved.
- Family-only evidence can create only a family-level proposal.
- Ambiguous and insufficient evidence is preserved in review output rather
  than converted into a precise relationship.
- The review workbooks remain disposable local artifacts and never update
  `35 Compatibility Matrix` or another protected source.

## Alternatives considered

- Treat compatibility as an attribute on a device, service, or part: rejected
  because a relationship has its own evidence, granularity, status, and
  lifecycle.
- Infer exact relationships from names: rejected because naming evidence is
  incomplete and can produce unsafe repair recommendations.
- Restart or compact the ID namespace: rejected because canonical identities
  are immutable and may already be referenced.

## References

- `Documentation/MASTER_COMPATIBILITY_SPEC.md`
- `Documentation/MASTER_COMPATIBILITY_DATA_DICTIONARY.md`
- `Documentation/MASTER_COMPATIBILITY_VALIDATION_RULES.md`
- `Documentation/MASTER_CATALOG_ARCHITECTURE.md`
- `Documentation/ADR/ADR-006-canonical-master-catalog-baseline.md`
