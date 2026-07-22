# AI Context

Last updated: 2026-07-22

This file is the primary orientation document for ChatGPT, Codex, and human
contributors. Read it before making repository changes, followed by
`PROJECT_STATUS.md`, `DECISIONS.md`, and `NEXT_SESSION.md`.

## Project

Nocturnix Repair Platform is a Python 3.14 desktop repair-management application
using PySide6. Its current system of record is
`Data/Nocturnix_Master_Database.xlsm`. Workbook tables are loaded into pandas
DataFrames with openpyxl.

## Canonical shared memory

The canonical project-memory documents are the Markdown files directly under
`Documentation/`:

- `AI_CONTEXT.md`: stable orientation and working rules.
- `MASTER_DEVELOPMENT_PLAN.md`: ordered delivery plan.
- `ARCHITECTURE.md`: implemented and intended architecture.
- `PROJECT_STATUS.md`: verified present state.
- `DECISIONS.md`: durable decisions and rationale.
- `FUTURE_ENHANCEMENTS.md`: ideas outside the active milestone.
- `CHANGELOG.md`: chronological completed changes.
- `NEXT_SESSION.md`: immediate handoff and verification commands.
- [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md): observed workbook schema, temporary
  adapter contracts, canonical targets, and unresolved migration questions.
- [`BUSINESS_RULES.md`](BUSINESS_RULES.md): verified, broken/undefined, and approved
  target engine rules.
- [`ENGINE_REFACTOR_PLAN.md`](ENGINE_REFACTOR_PLAN.md): phased engine migration plan.
- [`ADR/`](ADR/): accepted architecture decisions governing the migration.

Older material under `Source/documentation/`, `Source/docs_not_used/`, nested
documentation folders, and `Backups/` is reference material until explicitly
consolidated. It must not override these canonical files.

## Current entry point

The supported application is the PySide6 GUI:

```powershell
.venv\Scripts\python Source\run_gui.py
```

After editable installation, the `nocturnix` console script resolves to the same
`gui.app.main_window.main` function. `Source/main.py` is a legacy console interface.

## Current dependency flow

```text
PySide6 GUI
  -> GUI services
  -> business services
  -> repositories
  -> shared dict[str, pandas.DataFrame]
  -> Excel workbook loader
```

`Application` in `Source/app.py` is the composition root. Repair workflows also use
`RepairManager`, domain engines, and `WorkflowManager` directly. Persistence from
DataFrames back to the workbook is not yet complete.

## Working rules

- Inspect before editing and preserve unrelated user changes.
- Keep GUI, business logic, repositories, and workbook I/O separated.
- Do not treat empty placeholder modules as completed features.
- Avoid destructive workbook operations and never seed over production data.
- Update `PROJECT_STATUS.md`, `DECISIONS.md`, `CHANGELOG.md`, and `NEXT_SESSION.md`
  whenever a development slice changes shared project knowledge.
- Record verified results, not estimated completion percentages.
- Use plain UTF-8 text and avoid decorative console glyphs that fail on Windows
  legacy encodings.

## Verified baseline

- The master workbook currently exposes 20 configured tables.
- `Application()` loads all 20 tables successfully after the ASCII console fix.
- Ruff currently passes for `Source/` under the configured rule set.
- Pyright and pytest still expose legacy/stale-code issues; see `PROJECT_STATUS.md`.
- The working tree contains an in-progress stabilization pass and must be reviewed
  before committing.
