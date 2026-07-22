# Project Status

Last updated: 2026-07-22
Version: 0.7.0 alpha
State: Active development; stabilization in progress

## Verified working

- Python 3.14 virtual environment exists.
- pandas 3.0.3, openpyxl 3.1.5, and PySide6 6.11.1 are installed.
- `Application()` loads all 20 configured workbook tables.
- Workbook-loader status output is plain ASCII and works on the Windows console.
- The supported GUI launcher resolves to `gui.app.main_window.main`.
- Root `pyproject.toml` declares runtime and development dependencies.
- Ruff passes for `Source/` with the configured rules.

## In progress

- A stabilization diff touches project configuration and multiple Ruff mechanical
  fixes. It has not yet been committed.
- Canonical documentation is being consolidated under `Documentation/`.
- Pyright environment configuration and genuine type errors need separation.
- Legacy smoke scripts need conversion or relocation before pytest can be a reliable
  gate.

## Known failures and risks

- Pyright currently reports missing third-party imports because it is not yet pointed
  at `.venv`, plus genuine errors in logging, seeder, technical-knowledge, and GUI
  code.
- Pytest collection fails because several `Source/tests/test_*.py` files execute
  outdated code at import time and reference removed attributes.
- `Source/logs/application_log.py` and `error_log.py` import a missing
  `logging_system` package.
- `TechnicalKnowledgeService` calls a nonexistent `GuideRepository.all_guides()`.
- `Source/managers/seeder_manager.py` targets an obsolete seeder API.
- Workbook writes and durable CRUD persistence remain incomplete.
- The repository contains many empty placeholders and duplicate implementations.
- `Source/nocturnix_repair_platform.egg-info/` is an untracked generated artifact
  from editable installation and should be ignored or removed.

## Current worktree scope

The active stabilization pass includes:

- Root `README.md` and `pyproject.toml`.
- Corrected `.gitignore` backup/lock-file lines.
- Import-safe `Source/run_gui.py` with direct execution preserved.
- ASCII-safe `TableLoader` output.
- Ruff-driven import and typing cleanup across active source.
- A behavior change in `RepairPage.add_repair()` that calls `dialog.exec()`; this
  should be explicitly accepted or reverted before commit.

## Next milestone

Produce a clean, reviewable baseline where Ruff passes, Pyright resolves the virtual
environment and active-code errors, pytest collects real tests only, and application
bootstrap remains green.
