# ADR-009: Master Devices Identity and Schema

- Status: Accepted
- Date: 2026-07-23

## Context

The legacy catalog contains 46 retained Device records. Those rows mix device
identity observations with condition and provisional monetary observations.
They do not provide consistently reliable model numbers, variants, generations,
network types, storage, memory, carrier, region, operating system, or support
relationships.

Read-only inspection of canonical worksheet `32 Devices` found 842 valid Device
IDs from `DEV000001` through `DEV000842`, no duplicate valid IDs, and no
malformed populated IDs.

## Decision

- Master Devices is the authoritative proposed catalog of device identities and
  taxonomy.
- It is not customer-owned equipment, serialized inventory, stock-on-hand,
  compatibility approval, service approval, parts approval, or pricing.
- Canonical Device IDs use prefix `DEV`, exactly six digits, and regex
  `^DEV\d{6}$`.
- New IDs continue after the highest valid ID read from canonical worksheet
  `32 Devices` at runtime.
- If the canonical source has no populated valid namespace, ADR-009 authorizes
  the empty namespace beginning at `DEV000001`.
- IDs are immutable, unique, never reused, and never renumbered.
- A missing, unreadable, or structurally invalid canonical ID source is a
  blocker; an empty but valid `Device ID` column uses the ADR-approved first ID
  and is not guessed.
- Malformed populated IDs are reported and excluded from sequence arithmetic.
- Duplicate valid canonical IDs are a blocker.
- Legacy Device SKU is an alias/reference only, never the canonical primary key.
- Device identity is reviewed independently from compatibility, service
  mapping, parts mapping, inventory, and pricing.
- Canonical import requires separate authorization.

## Accepted Schema

Accept the 48-column Master Devices schema documented in
`MASTER_DEVICES_DATA_DICTIONARY.md`.

## Consequences

- The current 46-row review population is expected to receive `DEV000843`
  through `DEV000888`.
- IDs are assigned deterministically in ascending Source Record Number order.
- Assigning an ID does not approve identity or any downstream relationship.
- Manufacturer is populated only from an exact canonical-name match.
- Device Family may be populated from an explicit legacy type such as
  `Device - Phone`; ambiguous taxonomy remains pending.
- No model, variant, hardware attribute, compatibility, service, parts, or
  pricing fact is invented.

## References

- `Documentation/MASTER_DEVICES_SPEC.md`
- `Documentation/MASTER_DEVICES_DATA_DICTIONARY.md`
- `Documentation/MASTER_DEVICES_VALIDATION_RULES.md`
- `Documentation/ADR/ADR-006-canonical-master-catalog-baseline.md`
