# ADR-002: Engines Own Calculation and Decision Rules

- Status: Accepted
- Date: 2026-07-22

## Context

Current engines mix business decisions with direct DataFrame lookup. Repositories
also duplicate compatibility and inventory filtering. A stable boundary is needed
before workbook schemas and engine contracts are migrated.

## Decision

- Repositories own data retrieval, filtering, schema mapping, and record selection.
- Engines own compatibility decisions, pricing calculations, inventory sufficiency
  decisions, quote calculations, and validation of calculation inputs.
- Engines should receive explicit values or repository results and should not know
  workbook names, DataFrame column aliases, or openpyxl.
- Services coordinate repositories and engines; workflows own multi-step process state.

## Consequences

- Engines become independently testable with ordinary values.
- Repository adapters can isolate temporary workbook column aliases.
- Existing `EngineBase` data-access helpers become candidates for controlled
  retirement.
- Migration requires tests before direct database access is removed.

## Alternatives considered

- Keep all logic in repositories: rejected because pricing and compatibility decisions
  are business rules, not data access.
- Keep direct DataFrame access in engines: rejected because schema drift currently
  breaks runtime behavior.
- Move all rules into services: rejected because focused engines provide reusable,
  testable calculation boundaries.
