# Decisions

Last updated: 2026-07-22

## D-001: Canonical shared memory

Decision: Markdown files directly under `Documentation/` are the authoritative
project-memory documents.

Rationale: Status and architecture information currently exists in several stale,
conflicting trees. One predictable location lets ChatGPT, Codex, and contributors
start from the same facts.

## D-002: Supported application entry point

Decision: The PySide6 GUI is the supported application. `Source/run_gui.py` and the
installed `nocturnix` console script must resolve to `gui.app.main_window.main`.
`Source/main.py` remains a legacy console interface.

Rationale: The repository already has a functioning Qt application, while the
console controller depends on legacy UI modules.

## D-003: Excel remains the current system of record

Decision: Continue using `Data/Nocturnix_Master_Database.xlsm` during stabilization.
Do not migrate storage until repository/service boundaries and persistence tests are
stable.

Rationale: A premature database migration would combine architectural repair with a
high-risk data migration.

## D-004: Plain console output

Decision: Startup and diagnostic console output should use plain ASCII.

Rationale: Unicode checkmarks failed under the active Windows CP1252 console and
masked successful workbook loading.

## D-005: Tooling configuration

Decision: `pyproject.toml` is the source of truth for runtime dependencies, optional
development tools, packaging, Ruff, Pyright, and pytest configuration.

Rationale: The project previously had no reproducible dependency or analysis setup.

## D-006: Evidence-based status

Decision: Project status records verified capabilities and known failures, not
subjective completion percentages.

Rationale: Earlier status files disagreed substantially and overstated completion.

## Pending decisions

- Which workbook/table manager implementation becomes canonical?
- Should `RepairPage.add_repair()` display the dialog now or retain prior behavior
  until the repair workflow is complete?
- Should legacy smoke scripts be converted to pytest or moved under a scripts/manual
  QA directory?
- Which empty placeholder modules should be removed, retained, or formally planned?
