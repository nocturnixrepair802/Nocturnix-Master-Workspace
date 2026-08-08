# Master Development Plan

Last updated: 2026-07-22

## Objective

Deliver a reliable desktop repair-management application with a clear layered
architecture, controlled Excel persistence, tested repair workflows, and an
installable PySide6 user interface.

## Documentation preparation

- [x] Inventory the current workbook schema and distinguish current, adapter, and
  canonical target contracts in [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).
- [x] Record verified, broken/undefined, and approved target engine rules in
  [BUSINESS_RULES.md](BUSINESS_RULES.md).
- [x] Record the accepted repository, engine, facade, Excel, and money decisions in
  [ADR/](ADR/).
- [ ] Phase 0 tests and source refactoring have not started.

## Phase 1: Stabilize the development baseline

- [x] Add root project metadata and dependency declarations.
- [x] Define the PySide6 GUI as the supported entry point.
- [x] Make workbook-loader console output ASCII-safe.
- [x] Configure Ruff, Pyright, and pytest.
- [x] Establish canonical shared-memory documents.
- [ ] Point Pyright at the repository virtual environment and resolve genuine
  source errors.
- [ ] Separate or convert legacy executable smoke scripts named `test_*.py`.
- [ ] Review the current lint-generated diff and remove generated packaging
  artifacts from source control scope.

Exit criterion: clean Ruff, usable Pyright baseline, deterministic pytest
collection, successful 20-table application bootstrap, and documented launch steps.

## Phase 2: Consolidate architecture

- Select one workbook manager and one table manager implementation.
- Remove or archive duplicate seeder-manager and logger implementations.
- Move workbook I/O out of the business-service layer.
- Define repository and service protocols with consistent method names.
- Classify empty modules as package markers, planned work, or obsolete scaffolding.

Exit criterion: one documented dependency path with no competing active
implementations.

## Phase 3: Implement safe persistence

- Add workbook and table write operations.
- Preserve `.xlsm` VBA content and Excel table ranges.
- Add transaction/backup behavior before saves.
- Validate schema, relationships, and identifiers before persistence.
- Test against disposable workbook fixtures.

Exit criterion: create, edit, and delete operations persist safely and are covered
by automated tests.

## Phase 4: Complete repair workflow

- Repair intake and ticket-number generation.
- Customer/device selection and validation.
- Quote, labor, part, compatibility, and inventory integration.
- Edit, status transitions, completion, invoicing, and audit history.

Exit criterion: a repair can move from intake to completion and persist correctly.

## Phase 5: Operational modules

- Inventory and suppliers.
- Estimates, invoices, and payments.
- Dashboard and reporting.
- Settings, user management, and installer.

## Quality gates for every phase

- Ruff passes.
- Pyright has no unexplained errors in active code.
- Pytest collection and relevant tests pass.
- Application bootstrap succeeds.
- GUI changes receive focused manual verification.
- Canonical shared-memory documents are updated.

Implementation sequencing for the engine work is maintained in the
[Engine Refactor Plan](ENGINE_REFACTOR_PLAN.md).
