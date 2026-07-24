# Project Status

Last updated: 2026-07-23
Version: 0.7.0 alpha
State: Active development; stabilization in progress

## Phase 2 canonical shadow-import milestone

- Phase 2 Canonical Data Integration Architecture is complete.
- `Source/import_engine/` provides an application-independent Import Engine,
  read-only approved-workbook validator, structured release manifest, and isolated
  SQLite shadow store.
- Approved Service Type Normalization v1.0 remains protected by exact SHA-256
  verification before validation, after read-only extraction, and before returning
  an idempotent prior manifest.
- Exact worksheet/table schemas, row counts, row-status distributions, governed
  identifiers, canonical references, and the `SVC000343` exclusion reconcile before
  persistence.
- Shadow tables contain 77 Canonical Service Types, 17 aliases, 313 Service
  normalization rows, and 265 Labor normalization rows.
- Every imported row retains source workbook, approved version, source SHA-256,
  worksheet/table, source row identity/number, import timestamp, exact source status,
  row digest, and lossless raw payload.
- Database constraints require `activation_approved = 0`, `runtime_active = 0`, and
  `imported_status = SHADOW_REFERENCE`.
- No runtime repository, application composition, production database read, pricing,
  compatibility, quote, or repair workflow consumes the shadow tables.
- Architecture, sequence, class, state-machine, rollback, and test-plan documentation
  is recorded in
  [CANONICAL_DATA_INTEGRATION_ARCHITECTURE.md](CANONICAL_DATA_INTEGRATION_ARCHITECTURE.md).
- Row-level import and activation governance is recorded in
  [SERVICE_TYPE_IMPORT_READINESS_CONTRACT.md](SERVICE_TYPE_IMPORT_READINESS_CONTRACT.md).

## Service Type Normalization QA milestone

- Service Type Normalization review is complete.
- Review v1.3 passed the read-only QA validator with 0 errors and 0 warnings.
- The validated review contains 313 populated Service Normalization records.
- Approved production release v1.0 was created at
  `D:\Business Portal\300_Pricing\Approved\Nocturnix_Service_Type_Normalization_Approved_v1.0.xlsx`.
- Validated source SHA-256:
  `DD9DE1EC80BAAED00ABA14976C12755C3E55DBBF68EF69556037BFF23E5E1B11`.
- Final approved-release SHA-256:
  `DE0F0957F687DF4866A2D06C4DF85A542FF58B61897481741EB1E6A04D825FBA`.
- QA reports:
  `Output\Nocturnix_Service_Type_Normalization_Approved_v1.0_QA.md` and
  `Output\Nocturnix_Service_Type_Normalization_Approved_v1.0_QA.json`.
- Release date: 2026-07-23.
- Only Import Metadata changed for release; all service mappings and all
  non-metadata worksheet content and structure were preserved.

## Session closeout

- Phase 0 is complete.
- Phase 1A compatibility stabilization is complete.
- Phase 2 canonical shadow import is complete.
- Phase 1B has not started.
- Phase 2 is ready for the closeout commit and annotated milestone tag.

## Verified working

- Python 3.14 virtual environment exists.
- pandas 3.0.3, openpyxl 3.1.5, and PySide6 6.11.1 are installed.
- `Application()` loads all 20 configured workbook tables.
- Workbook-loader status output is plain ASCII and works on the Windows console.
- The supported GUI launcher resolves to `gui.app.main_window.main`.
- Root `pyproject.toml` declares runtime and development dependencies.
- Ruff passes for `Source/` with the configured rules.

## In progress

- Competitive Pricing discovery is the next read-only work item. Pricing entry and
  Phase 1B runtime stabilization have not started.
- Pricing workbook readiness, missing inputs, identifier alignment, and unresolved
  business rules must be assessed before pricing implementation.
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

- Phase 2 Ruff checks: passed.
- Phase 2 focused Pyright: 0 errors, 0 warnings.
- Import Engine tests: 8 passed.
- Maintained `Tests/` suite: 52 passed and 1 xfailed.
- Remaining expected failure: rejection of negative pricing inputs.
- Approved-release temporary integration import: passed with exact
  77/17/313/265 shadow counts, `314 = 313 + 1` Service reconciliation,
  0 runtime-active rows, and 0 rows missing provenance.
- Approved workbook SHA-256 matched before and after integration validation.
- The four `Source/tests/` collection failures remain the pre-existing outdated
  manager/workflow attribute references documented under Known failures and risks;
  Phase 2 does not modify those paths.
- `git diff --check`: passed.

## Next milestone

Resume Competitive Pricing with read-only workbook and supporting-script discovery.
Do not enter or infer pricing values until workbook readiness, source evidence,
identifier alignment, and business-rule decisions are documented.
