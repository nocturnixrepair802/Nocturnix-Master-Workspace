# ADR-011: Master Labor Standards Governance

- Status: Accepted
- Date: 2026-07-23

## Context

The existing Labor Standards workbook contains operational labor observations
used by Master Services and Master Pricing. It is not yet governed as a
standalone review catalog with a protected identity namespace, explicit
provenance, review lifecycle, and reproducible validation contract.

Labor standards describe expected repair work. They are not technician
schedules, payroll records, timekeeping records, labor rates, prices, or proof
that a particular technician completed work.

## Decision

- Master Labor is the authoritative review catalog for labor standards
  referenced by Services.
- Source identifiers such as `NSLC-001` are legacy aliases. They are preserved
  exactly in `Legacy Labor ID` and are never validated or used as governed
  Labor Standard IDs.
- Canonical Labor Standard IDs use prefix `LAB`, exactly six digits, and regex
  `^LAB\d{6}$`.
- The generator inspects only an explicitly governed `Labor Standard ID`
  column for existing `LAB######` identifiers. A source `Labor ID` column
  containing `NSLC-*` values is legacy lineage, not the governed namespace.
- If no explicitly governed column exists, or that column contains no
  populated IDs, ADR-011 authorizes the empty namespace beginning at
  `LAB000001`. Otherwise allocation begins after the highest valid governed ID.
- Existing populated IDs must be valid, unique, and strictly increasing in
  workbook order. Malformed values are reported only from the explicitly
  governed column; duplicate or out-of-order governed IDs are blockers.
- Every protected source row must have a unique, nonblank Legacy Labor ID and
  unique source-row lineage.
- Generated IDs are continuous, unique, ordered, and nonoverlapping with the
  protected namespace. IDs are immutable, never reused, and never renumbered.
- Accept the 31-column review schema documented in
  `MASTER_LABOR_DATA_DICTIONARY.md`.
- Source labor values are copied only when explicitly present. The generator
  does not infer minutes, tiers, skill, difficulty, requirements, warranty, or
  approval.
- Generated records begin `Pending Review`. Blank controlled facts remain
  blank and are routed for review.
- Labor mapping is a separate review artifact with one row per Service. A
  suggested candidate always references a governed `LAB######` ID. An
  `NSLC-*` alias may support the evidence but is never the governed mapping.
- Master Services is never overwritten. Canonical import requires a separate
  authorized migration, backup, validation, approval, and rollback plan.

## Consequences

- The output is a disposable governed review artifact at
  `D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Labor_Catalog_v1.xlsx`.
- Allocating a `LAB######` Labor Standard ID does not approve labor content,
  minutes, difficulty, skill, tier, warranty, service mapping, pricing,
  canonical import, or replacement of a legacy alias.
- Unknown facts remain visible rather than being completed with estimates.
- Protected inputs are hash-checked before and after generation.
- Existing Master Services, Pricing, Parts, Devices, Compatibility, canonical
  workbooks, catalog workbooks, schemas, and validators remain unchanged.

## Alternatives considered

- Continue using an ungoverned labor workbook directly: rejected because
  identity, provenance, review state, and validation are not explicit.
- Infer missing labor facts from names or adjacent records: rejected because
  repair time and capability facts require accountable evidence.
- Update Master Services automatically from mapping scores: rejected because a
  suggested mapping requires human review and separate authorization.

## References

- `Documentation/MASTER_LABOR_SPEC.md`
- `Documentation/MASTER_LABOR_DATA_DICTIONARY.md`
- `Documentation/MASTER_LABOR_VALIDATION_RULES.md`
- `Documentation/ADR/ADR-006-canonical-master-catalog-baseline.md`
- `Documentation/ADR/ADR-010-master-compatibility-governance.md`
