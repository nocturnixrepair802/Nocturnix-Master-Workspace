# Changelog

All notable project changes should be recorded here. Entries describe completed or
actively reviewed work; planned work belongs in `MASTER_DEVELOPMENT_PLAN.md`.

## Unreleased - 2026-07-22

### Added

- Root `pyproject.toml` with packaging, dependency, Ruff, Pyright, and pytest
  configuration.
- Root `README.md` with setup and GUI launch instructions.
- Canonical shared-memory documentation under `Documentation/`.
- Installed project console entry point named `nocturnix`.

### Changed

- `Source/run_gui.py` can be imported safely and still launches the PySide6 app when
  executed directly.
- Workbook-loader status messages use ASCII output.
- Python typing and import ordering were modernized with Ruff.
- `RepairPage.add_repair()` currently executes the created repair dialog; this
  behavioral change remains pending explicit review.

### Fixed

- Removed malformed literal `'n` fragments from `.gitignore`.
- Preserved ignore rules for backups, virtual environments, Python caches, and byte
  code.
- Fixed Windows console failure caused by Unicode loader status glyphs.

### Verification

- Ruff passes.
- All 20 configured workbook tables load successfully.
- Pyright and pytest baselines were captured; remaining failures are documented in
  `PROJECT_STATUS.md`.

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
