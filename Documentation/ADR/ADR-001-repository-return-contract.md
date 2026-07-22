# ADR-001: Repository Return Contract

- Status: Accepted
- Date: 2026-07-22

## Context

Repositories are DataFrame-backed and currently expose a mixture of collection and
single-record operations. Callers need predictable return types, and repositories
must remain data-access components rather than implicit domain-model factories.

## Decision

- Collection queries return `pandas.DataFrame`.
- Single-record queries return `pandas.Series | None`.
- Repositories do not construct domain models by default.
- Domain mapping belongs in a service, workflow, or explicit mapping layer.
- Repositories should return copies where caller mutation would otherwise change
  repository state unintentionally.

## Consequences

- Service and GUI code can type and handle repository results consistently.
- pandas remains visible at the repository boundary during the current architecture.
- A future move away from pandas will require an explicit contract migration.
- Existing methods that violate this standard require inventory and staged migration.

## Alternatives considered

- Return domain models from every repository: rejected because most models are
  incomplete and it would couple data access to model construction.
- Return dictionaries: rejected because it loses current pandas operations without
  solving schema consistency.
- Allow each repository to choose: rejected because it preserves ambiguity.
