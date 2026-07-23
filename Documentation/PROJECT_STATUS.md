# Project Status

Last updated: 2026-07-23
Version: 0.7.0 alpha
State: Active development; stabilization in progress

## Session closeout

- Phase 0 is complete.
- Phase 1A compatibility stabilization is complete.
- Phase 1B has not started.
- `main` is synchronized with `origin/main` at commit
  `139145bc5b558bbd599c33c7168be16a079052ba` (`139145b`).
- The current milestone tag is `v0.3.0-alpha`, which points to the current HEAD.
- The repository was clean before this documentation-only closeout.

## Verified working

- Python 3.14 virtual environment exists.
- pandas 3.0.3, openpyxl 3.1.5, and PySide6 6.11.1 are installed.
- `Application()` loads all 20 configured workbook tables.
- Workbook-loader status output is plain ASCII and works on the Windows console.
- The supported GUI launcher resolves to `gui.app.main_window.main`.
- Root `pyproject.toml` declares runtime and development dependencies.
- Ruff passes for `Source/` with the configured rules.

## In progress

- Phase 1B pricing stabilization is the next planned engine slice, but it has not
  been approved or started.
- Pricing business-rule questions must be resolved before Phase 1B implementation.
- The Master Pricing review package is documentation-first and remains
  uncommitted. ADR-007 resolves pricing-record identity and approves its
  47-column schema; generator execution and workbook creation have not occurred.

## Master Pricing review milestone

- `PRC######` is the accepted Pricing Record ID namespace.
- The current empty namespace begins at `PRC000001`; the 314-row draft is
  expected to end at `PRC000314`.
- `Legacy Pricing Status` preserves the Master Services observation, while
  `Pricing Status` owns the governed pricing lifecycle.
- Initial records are draft review records. Calculated fields and Final Customer
  Price remain blank and unapproved.
- Currency, cost, margin, regional-market, calculation, rounding, approval,
  effective-date, and publication policies remain unresolved.
- No canonical workbook import or pricing-engine change is authorized.

## Engine refactor documentation baseline

- The 20 configured workbook tables are inventoried in
  [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).
- Current, broken/undefined, and approved target rules are recorded in
  [BUSINESS_RULES.md](BUSINESS_RULES.md).
- Seven accepted architecture decisions are recorded under [ADR/](ADR/).
- [ENGINE_REFACTOR_PLAN.md](ENGINE_REFACTOR_PLAN.md) is being implemented in bounded
  phases.
- Phase 0 added typed result definitions and characterization tests.
- Phase 1A is complete and stabilizes the compatibility path through a temporary repository adapter
  over the unchanged workbook columns `Device Family` and `Service Name`.
- `CompatibilityEngine` returns `CompatibilityResult`, honors `Supported=False`,
  rejects malformed decisions, and preserves `Notes` and `Requires Capability`.
- Pricing and inventory stabilization, workbook migration, and canonical column
  renaming have not begun.

## Known failures and risks

- Pyright currently reports missing third-party imports because it is not yet pointed
  at `.venv`, plus genuine errors in logging, seeder, technical-knowledge, and GUI
  code.
- Pytest collection fails because several `Source/tests/test_*.py` files execute
  outdated code at import time and reference removed attributes.
  The unrelated failing references are `RepairManager.repositories`,
  `RepositoryManager.services`, `ServiceManager.suppliers`, and
  `WorkflowManager.repair` (the current attribute is `repairs`).
- `Source/logs/application_log.py` and `error_log.py` import a missing
  `logging_system` package.
- `Source/managers/seeder_manager.py` targets an obsolete seeder API.
- Workbook writes and durable CRUD persistence remain incomplete.
- The repository contains many empty placeholders and duplicate implementations.
- `Source/nocturnix_repair_platform.egg-info/` is an untracked generated artifact
  from editable installation and should be ignored or removed.

## Closeout validation

- Ruff: passed.
- Focused Pyright for Phase 1A files: 0 errors and 0 warnings.
- Phase 0 and Phase 1A tests: 37 passed and 1 strict xfailed.
- Remaining strict xfail: rejection of negative pricing inputs.
- Application startup smoke test: passed; 20 tables loaded and compatibility
  repository/engine sharing verified.
- `git diff --check`: passed before the documentation closeout edits.

## Next milestone

Begin Phase 1B pricing stabilization only after reviewing and resolving the pricing
business-rule questions recorded in the next-session handoff.
