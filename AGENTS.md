# AGENTS.md

## Project overview
- This repository contains a Python catalog-generation workflow that reads an Excel workbook, validates its sheets, and produces catalog/export artifacts.
- The main project root is the repository root, but the runtime context for execution is the Source folder.
- Core paths are defined in [Source/config.py](Source/config.py), and the expected workbook lives in [Data/Nocturnix_Master_Database.xlsm](Data/Nocturnix_Master_Database.xlsm).

## Repository layout
- [Source/main.py](Source/main.py): entry point for the application.
- [Source/services](Source/services): pipeline steps such as workbook loading, pricing, SKU generation, and Square export.
- [Source/models](Source/models): data classes used by the pipeline.
- [Source/validators](Source/validators): workbook validation logic.
- [Source/utilities](Source/utilities): shared helpers and logging.
- [Output](Output): generated export files.
- [Logs](Logs): runtime logs.

## Working conventions
- Keep new logic in the module that owns the responsibility. For example, workbook I/O belongs in the services layer, while validation belongs in [Source/validators/workbook_validator.py](Source/validators/workbook_validator.py).
- Preserve the existing workbook sheet names and expected structure. The loader and validator are tightly coupled to the workbook schema.
- Prefer small, focused functions and classes over large monolithic modules.
- When a change affects the data pipeline, update the related service and validator together.

## Notes for changes
- If you add or rename workbook sheets, update both the loader and validator in the same change.
- Keep generated artifacts under [Output](Output) and logging under [Logs](Logs) unless the task clearly requires otherwise.
- The project currently relies on Python, pandas, and openpyxl. If a change introduces a new dependency, make that explicit in the relevant module or documentation.
- There is no formal test suite in this repository yet, so validation is primarily through running the application and checking the outputs.

## Validation guidance
- Before finishing a change that affects runtime behavior, run the application from the Source folder with: python main.py
- If the change touches data loading or validation, also verify that the expected workbook sheets are still recognized correctly.
