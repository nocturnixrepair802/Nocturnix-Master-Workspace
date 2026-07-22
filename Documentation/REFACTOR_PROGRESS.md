# Engine Refactor Progress

Last updated: 2026-07-22

This document records completed implementation phases from
[ENGINE_REFACTOR_PLAN.md](ENGINE_REFACTOR_PLAN.md). Planned work is not described as
current behavior.

## Phase 0 - Complete

- Added infrastructure-independent typed engine result definitions.
- Added characterization tests for compatibility, pricing, inventory, quotes, and
  manager-to-engine contract mismatches.
- Preserved known defects as explicit exceptions or strict expected failures.

## Phase 1A - Complete

- Added `CompatibilityRepository.find_service(device_family_code, service_id)` as
  an internal adapter over the unchanged workbook columns `Device Family` and
  `Service Name`.
- Added descriptive failures for missing compatibility columns and duplicate
  family/service matches.
- Changed `CompatibilityEngine` to consume the repository and return
  `CompatibilityResult`.
- Implemented explicit boolean `Supported` handling, notes-based reasons, required
  capability preservation, and unsupported no-match results.
- Added `RepairManager.validate_service()` and retained the deprecated
  `validate_part()` compatibility shim.
- Injected the shared compatibility engine into `QuoteEngine` and retained an
  explicit temporary dictionary conversion for existing quote callers.
- Converted only implemented compatibility expectations from strict expected
  failures into passing tests. The unrelated negative-pricing expected failure
  remains.

The workbook and its column names remain unchanged. Pricing, inventory, GUI,
workflow, and `EngineBase` stabilization have not begun.

## Next phase

Phase 1B requires a separate copy-paste-ready implementation instruction. No Phase
1B work is approved by this status entry.

## Session closeout baseline

- Repository milestone: `v0.3.0-alpha` at `139145b`.
- Phase 0: complete.
- Phase 1A: complete.
- Phase 1B: not started.
- Ruff: passed.
- Focused Phase 1A Pyright: 0 errors and 0 warnings.
- Focused tests: 37 passed and 1 strict xfailed.
- Remaining strict xfail: negative pricing input rejection.
- Application smoke test: passed with all 20 tables loaded.
- Existing unrelated full-suite collection errors reference
  `RepairManager.repositories`, `RepositoryManager.services`,
  `ServiceManager.suppliers`, and `WorkflowManager.repair` instead of `repairs`.
