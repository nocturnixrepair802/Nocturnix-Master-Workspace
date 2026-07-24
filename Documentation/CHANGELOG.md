# Changelog

All notable project changes should be recorded here. Entries describe completed or
actively reviewed work; planned work belongs in `MASTER_DEVELOPMENT_PLAN.md`.

## Unreleased - 2026-07-23

### Added

- First approved Service Type Normalization production workbook:
  `Nocturnix_Service_Type_Normalization_Approved_v1.0.xlsx`.
- Reusable worksheet-specific Excel QA validation with configurable checks for
  structure, populated rows, business rules, validations, and freeze panes.
- SHA-256 integrity verification for validated source and approved release
  workbooks, including read-only validator before/after checks.
- Root `pyproject.toml` with packaging, dependency, Ruff, Pyright, and pytest
  configuration.
- Root `README.md` with setup and GUI launch instructions.
- Canonical shared-memory documentation under `Documentation/`.
- Installed project console entry point named `nocturnix`.
- Phase 0 infrastructure-independent typed engine results and characterization tests.
- A canonical `CompatibilityRepository.find_service()` lookup over the unchanged
  workbook's `Device Family` and `Service Name` columns.
- `RepairManager.validate_service()` returning `CompatibilityResult`.
- ADR-007 accepting the `PRC######` Master Pricing identity namespace and the
  47-column Master Pricing review schema.
- Documentation-first Master Pricing generator and independent validator.

### Changed

- Validated 313 Service Normalization records after removing incomplete
  placeholder `SVC000343`.
- Corrected workbook freeze panes to `A2` for the Instructions and Service
  Normalization worksheets.
- Published Service Type Normalization Approved v1.0 from validated review v1.3.
- Approved release metadata records version v1.0, review source v1.3, QA PASS,
  validation date 2026-07-23, and the validated source SHA-256.
- `Source/run_gui.py` can be imported safely and still launches the PySide6 app when
  executed directly.
- Workbook-loader status messages use ASCII output.
- Python typing and import ordering were modernized with Ruff.
- `RepairPage.add_repair()` currently executes the created repair dialog; this
  behavioral change remains pending explicit review.
- Phase 1A makes `CompatibilityEngine` consume `CompatibilityRepository`, honor
  boolean `Supported` values, and preserve notes and required capabilities.
- `RepairManager` and `QuoteEngine` now share one injected compatibility engine;
  quote dictionaries temporarily adapt the typed compatibility result.
- Master Pricing may allocate `PRC000001` from the ADR-007-approved empty
  namespace and later continue after the highest valid canonical PRC ID.
- `RepairManager.validate_part()` remains as a deprecated compatibility alias while
  existing references are retired.

### Fixed

- Removed malformed literal `'n` fragments from `.gitignore`.
- Preserved ignore rules for backups, virtual environments, Python caches, and byte
  code.
- Fixed Windows console failure caused by Unicode loader status glyphs.
- Compatibility lookups now report missing required columns and duplicate matches
  descriptively instead of raising a raw `KeyError` or selecting a row silently.

### Engine refactor progress

- Phase 1A is complete. The compatibility path now uses an internal translation
  layer over the unchanged workbook schema, while temporary caller shims remain
  explicitly marked for removal after canonical workbook migration.

### Verification

- Service Type Normalization review v1.3 and approved v1.0 both passed the
  read-only QA validator with 0 errors and 0 warnings.
- Structural comparison confirmed that the approved release preserved all
  service mappings and all non-metadata workbook content from review v1.3.
- Approved-release SHA-256:
  `DE0F0957F687DF4866A2D06C4DF85A542FF58B61897481741EB1E6A04D825FBA`.
- Session closeout at `v0.3.0-alpha` / `139145b` confirmed `main` synchronized with
  `origin/main` and a clean pre-closeout working tree.
- Ruff passed and focused Phase 1A Pyright reported 0 errors and 0 warnings.
- Phase 0 and Phase 1A tests reported 37 passed and 1 strict xfailed; the remaining
  expected failure covers negative pricing inputs.
- The application startup smoke test loaded all 20 configured workbook tables and
  verified shared compatibility repository and engine ownership.
- `git diff --check` passed before the documentation-only closeout changes.

## Historical summary

- Sprint 1: project foundation.
- Sprint 2: Excel database and loading framework.
- Sprint 3: customer module foundation.
- Sprint 4: device catalog and lookup integration.
- Sprint 5: repository/service/application composition architecture.
- Sprint 6: repair-module foundation.
- Sprint 7: repair integration and in-memory seeder framework.

Detailed historical documents remain under `Source/documentation/` until archival
consolidation is complete.
