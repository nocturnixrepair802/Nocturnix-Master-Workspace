# Next Session

Last updated: 2026-07-22

## Start here

1. Read `AI_CONTEXT.md`, `PROJECT_STATUS.md`, and `DECISIONS.md`.
2. Read [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md),
   [BUSINESS_RULES.md](BUSINESS_RULES.md),
   [ENGINE_REFACTOR_PLAN.md](ENGINE_REFACTOR_PLAN.md), and the accepted
   [architecture decisions](ADR/) before engine work.
3. Run `git status --short` and inspect the full stabilization diff.
4. Do not delete legacy or duplicate files until their active references are checked.

## Immediate objective

Finish and review the stabilization baseline without expanding feature scope.

The engine documentation-preparation stage is complete. Do not begin Phase 0 tests,
source refactoring, workbook migration, or column renames without a separate approved
task.

## Ordered tasks

1. Decide whether to retain or revert `dialog.exec()` in
   `Source/gui/pages/repair_page.py`; it is a behavior change, not just lint cleanup.
2. Add the virtual-environment location to Pyright configuration and rerun Pyright.
3. Fix genuine active-code errors:
   - missing `logging_system` imports;
   - `GuideRepository.all_guides()` mismatch;
   - obsolete `managers/seeder_manager.py` API;
   - optional DataFrame access in `customer_page.py`.
4. Move or convert import-time legacy smoke scripts so pytest collects real tests.
5. Ignore/remove the generated `Source/nocturnix_repair_platform.egg-info/` artifact.
6. Re-run the complete verification set and review the diff before committing.

## Verification commands

```powershell
.venv\Scripts\ruff.exe check Source --no-cache
.venv\Scripts\pyright.exe
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -c "import sys; sys.path.insert(0, 'Source'); from app import Application; Application()"
git diff --check
git status --short
```

## Expected baseline

- Ruff: currently passes.
- Application bootstrap: currently loads 20 of 20 tables.
- Pyright: currently fails; distinguish environment resolution from real errors.
- Pytest: currently fails during collection on outdated script-style tests.

## Handoff note

The editable install created files inside `.venv` and an untracked egg-info directory
under `Source/`. No repository commit has been made during the stabilization pass.
