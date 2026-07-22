# ADR-003: RepairManager Remains the Repair Facade

- Status: Accepted
- Date: 2026-07-22

## Context

`RepairManager` is already owned by `Application` and consumed by workflows. Its
current method names and engine composition contain contract problems, but removing
the manager during schema migration would create unnecessary caller disruption.

## Decision

- `RepairManager` remains the caller-facing facade throughout the engine migration.
- Its public methods will be corrected incrementally to express device-family/service
  compatibility, numeric pricing inputs, inventory availability, and quote generation.
- Compatibility aliases or deprecation paths may be used temporarily.
- `RepairManager` owns shared engine instances and injects them into `QuoteEngine` in
  the target composition.
- It does not absorb repository behavior or workflow state.

## Consequences

- Workflows retain a stable integration point.
- Contract corrections can be phased rather than applied to every caller at once.
- Temporary aliases must have removal criteria to avoid permanent duplicate APIs.
- Engine construction becomes explicit and testable.

## Alternatives considered

- Remove `RepairManager` and call engines directly: rejected because it broadens the
  migration and couples callers to engine composition.
- Move all behavior into `RepairService`: rejected for now because it combines two
  architectural migrations and disrupts workflows.
- Preserve current signatures indefinitely: rejected because their semantics are
  incorrect.
