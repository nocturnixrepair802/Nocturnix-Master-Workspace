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
