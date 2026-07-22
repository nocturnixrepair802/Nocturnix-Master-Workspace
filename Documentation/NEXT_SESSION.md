# Next Session

Last updated: 2026-07-22

## Start here

1. Run `git pull`.
2. Read [AI_CONTEXT.md](AI_CONTEXT.md).
3. Read [ENGINE_REFACTOR_PLAN.md](ENGINE_REFACTOR_PLAN.md).
4. Read [REFACTOR_PROGRESS.md](REFACTOR_PROGRESS.md).
5. Confirm the repository is clean and review the current validation baseline.

## Current baseline

- Phase 0 is complete.
- Phase 1A compatibility stabilization is complete.
- Phase 1B has not started.
- Current milestone: `v0.3.0-alpha` at commit `139145b`.
- At closeout, `main` matched `origin/main` and the working tree was clean.
- Focused validation: Ruff passed, Pyright reported 0 errors and 0 warnings, 37
  tests passed, 1 strict pricing xfail remained, the application loaded all 20
  tables, and `git diff --check` passed.

## Immediate objective

Begin Phase 1B pricing stabilization only after receiving a copy-paste-ready
implementation instruction. Do not touch inventory, workbook schemas, GUI, or
workflows. Review and resolve the pricing business-rule questions before changing
implementation behavior.

## Phase 1B readiness checklist

- [ ] Confirm the meaning of `labor_rates.Labor Price`.
- [ ] Confirm the unit of `labor_rates.Estimated Time`.
- [ ] Confirm the markup formula.
- [ ] Confirm the processing-fee formula.
- [ ] Confirm tax handling.
- [ ] Confirm the rounding policy.
- [ ] Confirm the minimum labor charge.
- [ ] Confirm whether `retail_pricing` contains output values or pricing rules.

## Known unrelated test-collection failures

Legacy script-style tests still reference:

- `RepairManager.repositories`
- `RepositoryManager.services`
- `ServiceManager.suppliers`
- `WorkflowManager.repair` instead of `WorkflowManager.repairs`

These failures are outside Phase 1B pricing stabilization unless separately
approved.

## Working rule

After planning or review, wait for a copy-paste-ready implementation instruction.
Do not infer approval or begin Phase 1B from this handoff alone. Show the diff and
validation results after every approved task.
