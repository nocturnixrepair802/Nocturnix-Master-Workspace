# Nocturnix Migration Draft Remediation

`remediate_migration_draft.py` is a controlled workbook-remediation tool for migration-readiness findings. It is intentionally conservative: plan mode is the default, ambiguous mappings are never applied, and the source workbook is never overwritten.

## Safety Model

Before planning or applying, the tool:

- Calculates the source workbook SHA-256.
- Opens and inventories worksheets and Excel tables.
- Builds a remediation plan.
- Classifies every proposed action as `SAFE_AUTOMATIC`, `NEEDS_DECISION`, `BLOCKED`, or `AUDIT_RULE_ONLY`.
- Writes detailed plan and decision reports.
- Verifies the source workbook SHA-256 is unchanged before exit.

In apply mode, only `SAFE_AUTOMATIC` actions are applied to a new workbook saved in the output folder.

## Classification Meanings

- `SAFE_AUTOMATIC`: deterministic and safe to apply without business judgment.
- `NEEDS_DECISION`: requires governance or design approval before applying.
- `BLOCKED`: unsafe or impossible to apply because a required mapping or structure is missing, duplicated, or ambiguous.
- `AUDIT_RULE_ONLY`: issue is addressed by corrected audit logic rather than workbook edits.

## Plan-Only Workflow

Plan-only is the default:

```powershell
.\.venv\Scripts\python.exe .\remediate_migration_draft.py `
  "D:\Business Portal\01_Nocturnix_Business_Portal\100_Master_Data\Devices\Nocturnix_Master_Devices_Catalog_v1.5_Approved_ID_Migration_Draft_v1.3.xlsx" `
  --output-dir ".\migration_remediation_plan" `
  --plan-only
```

Plan-only mode writes reports but creates no workbook output.

## Apply Workflow

Controlled apply:

```powershell
.\.venv\Scripts\python.exe .\remediate_migration_draft.py `
  "D:\Business Portal\01_Nocturnix_Business_Portal\100_Master_Data\Devices\Nocturnix_Master_Devices_Catalog_v1.5_Approved_ID_Migration_Draft_v1.3.xlsx" `
  --output-dir ".\migration_remediation_apply" `
  --apply `
  --audit-script ".\audit_migration_draft.py"
```

The first apply run should not use `--refresh-control-sheets` or `--approve-schema-additions`.

## Reports

Each run writes:

- `remediation_summary.md`
- `remediation_plan.csv`
- `remediation_plan.json`
- `safe_mapping_changes.csv`
- `blocked_mappings.csv`
- `decisions_required.csv`
- `worksheet_rename_analysis.csv`
- `lookup_catalog_decisions.csv`
- `multi_value_fk_decisions.csv`
- `device_model_crosswalk_readiness.md`
- `registry_update_plan.csv`
- `source_workbook_sha256.txt`
- `execution_log.txt`

Apply mode also writes:

- a timestamped remediated workbook
- `remediated_workbook_sha256.txt`
- `post_remediation_audit\`

## Decision-File Workflow

Review `decisions_required.csv`, `lookup_catalog_decisions.csv`, and `multi_value_fk_decisions.csv` before any additional remediation. Fill `UserDecision` or governance approval fields outside the source workbook, then run a future controlled task that explicitly consumes those decisions.

## Rollback Guidance

The source workbook is never overwritten. To roll back an apply run, discard the generated remediated workbook and output folder. No source workbook rollback should be needed.

## Explicit Non-Actions

- Ambiguous mappings are never applied.
- Missing lookup tables are not invented.
- Business lookup values are not created.
- Multi-value foreign keys are not reduced to a single value.
- `tblDeviceModelIDCrosswalk` is not populated by this tool.
- Control-sheet refresh requires `--refresh-control-sheets`.
- Schema additions require `--approve-schema-additions`.
