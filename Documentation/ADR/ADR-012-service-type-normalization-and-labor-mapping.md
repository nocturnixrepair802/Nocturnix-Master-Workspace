# ADR-012: Service Type Normalization and Labor Mapping Governance

- Status: Accepted
- Date: 2026-07-23

## Context

Canonical worksheet `33 Service Types` contains a 28-row summary taxonomy in
columns B-H and a 70-row detailed taxonomy in columns L-T. Master Services uses
only three broad Repair Type values across 314 records, while Master Labor uses
30 Repair Type values across 265 records. Sixteen normalized Labor Repair Type
values match the detailed taxonomy exactly; fourteen require an explicit alias
decision or unresolved review.

The platform needs a governed operation vocabulary that preserves source labels,
separates service identity from labor definition, and prevents similarity or
convenience from becoming approval.

## Decision

- The detailed taxonomy in columns L-T of `33 Service Types` is authoritative
  for review. The summary taxonomy in columns B-H remains legacy/reference
  context.
- Service Type is a governed operation vocabulary.
- Service Name remains the device/model-specific commercial service label.
- Labor Standard remains a separate time and skill definition.
- Existing Service and Labor source values are preserved. Aliases add review
  evidence and never overwrite a source value.
- Fuzzy similarity may surface candidates in a future authorized workflow, but
  it cannot approve mappings. Version 1.0.2 uses no fuzzy mapping mechanism.
- Device Family must constrain labor selection. A labor row is eligible only
  when its family matches or it is explicitly universal.
- Manufacturer is optional and constrains selection only when labor differs
  materially and the Labor Standard is manufacturer-specific.
- Every generated normalization, alias, and labor relationship remains proposed
  and `Pending Review`. No generated row is `Approved`.
- The generator inspects explicit `Service Type ID` columns throughout the
  canonical workbook. If a complete governed `STY######` namespace exists for
  the detailed taxonomy, it is preserved.
- If no populated governed namespace exists, ADR-012 authorizes stable
  review-local IDs beginning at `STY000001`, with regex `^STY\d{6}$`, in
  detailed-taxonomy row order. Review-local IDs do not authorize canonical
  import.
- A partially populated governed namespace is a blocker; the generator does not
  mix governed and review-local identity.
- Canonical import requires separate authorization, backup, validation,
  approval, and rollback planning.

## Consequences

- Master Services, Master Labor, the canonical workbook, and the earlier labor
  mapping review remain protected read-only inputs.
- Broad and ambiguous source types remain visible in unresolved review.
- A Service-to-Labor suggestion requires canonical Service Type agreement plus
  Device Family and applicable Manufacturer agreement.
- When multiple Labor Standards remain eligible, no Labor Standard ID is
  assigned and the relationship is routed to unresolved review.
- The output is a disposable review artifact at
  `D:\Business Portal\300_Pricing\Working\Nocturnix_Service_Type_Normalization_Review_v1.xlsx`.

## Alternatives considered

- Rename Repair Type values in source workbooks: rejected because this destroys
  source lineage and bypasses review.
- Approve the nearest fuzzy label: rejected because lexical similarity is not
  evidence of equivalent repair scope.
- Treat Service Name, Service Type, and Labor Standard as one concept: rejected
  because commercial naming, operation vocabulary, and labor definition have
  different governance and lifecycles.
- Select the first eligible Labor Standard: rejected because deterministic
  ordering does not resolve business ambiguity.

## References

- `Documentation/SERVICE_TYPE_NORMALIZATION_SPEC.md`
- `Documentation/SERVICE_TYPE_ALIAS_DATA_DICTIONARY.md`
- `Documentation/SERVICE_TYPE_NORMALIZATION_VALIDATION_RULES.md`
- `Documentation/ADR/ADR-006-canonical-master-catalog-baseline.md`
- `Documentation/ADR/ADR-010-master-compatibility-governance.md`
- `Documentation/ADR/ADR-011-master-labor-standards-governance.md`
