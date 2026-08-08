# Nocturnix Migration Draft Audit

`audit_migration_draft.py` is a read-only Python audit tool for Nocturnix Master Devices Catalog migration draft workbooks. It inspects workbook structure, Excel tables, lookup catalog metadata, crosswalk metadata, primary keys, foreign keys, formulas, control-sheet staleness, and migration readiness.

The script never saves, edits, copies, normalizes, or repairs the source workbook.

## Requirements

- Python 3.12 or newer
- `openpyxl`
- Standard-library modules used by the script: `pathlib`, `hashlib`, `datetime`, `json`, `csv`, `collections`, and `re`

No pandas dependency is required or used.

## Install openpyxl

PowerShell example using a local virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install openpyxl
```

## Run The Audit

Basic usage:

```powershell
.\.venv\Scripts\python.exe .\audit_migration_draft.py "D:\Business Portal\01_Nocturnix_Business_Portal\100_Master_Data\Devices\Nocturnix_Master_Devices_Catalog_v1.5_Approved_ID_Migration_Draft_v1.3.xlsx"
```

Use a specific output folder:

```powershell
.\.venv\Scripts\python.exe .\audit_migration_draft.py "D:\Business Portal\01_Nocturnix_Business_Portal\100_Master_Data\Devices\Nocturnix_Master_Devices_Catalog_v1.5_Approved_ID_Migration_Draft_v1.3.xlsx" --output-dir ".\migration_audit_v13"
```

If `--output-dir` is omitted, the script creates a timestamped folder beside the script, such as:

```text
migration_audit_20260725_163000
```

## Output Files

Each run writes:

- `migration_audit_summary.txt`: concise text summary matching console output.
- `migration_audit_report.json`: machine-readable audit details and findings.
- `migration_audit_findings.csv`: all findings with severity, category, location, expectation, actual value, and recommended action.
- `table_inventory.csv`: all Excel tables, ranges, headers, row counts, styles, overlap and formula consistency checks.
- `worksheet_inventory.csv`: worksheet visibility, dimensions, table counts, naming checks, and whitespace checks.
- `lookup_catalog_audit.csv`: lookup catalog metadata validation.
- `crosswalk_catalog_audit.csv`: crosswalk catalog metadata validation.
- `primary_key_audit.csv`: primary-key counts, duplicate/blank/malformed ID checks.
- `foreign_key_audit.csv`: orphan, legacy-format, and multi-value foreign-key checks.
- `crosswalk_completeness.csv`: physical crosswalk table readiness and conflict summary.
- `formula_audit.csv`: formula counts and compatibility/volatility summary.
- `migration_readiness.md`: human-readable readiness summary.

## Finding Severities

- `PASS`: requirement is satisfied.
- `INFO`: informational observation requiring no correction.
- `WARNING`: potential inconsistency or governance weakness.
- `ERROR`: data or metadata issue requiring correction.
- `BLOCKER`: issue that makes migration unsafe or prevents reliable validation.

## Readiness Logic And Exit Codes

- `0`: READY
- `1`: READY WITH WARNINGS
- `2`: NOT READY
- `3`: script execution failure

Readiness is determined as follows: any `BLOCKER` or `ERROR` finding makes the workbook `NOT READY`; warnings without errors produce `READY WITH WARNINGS`; a clean audit produces `READY`.

If the source workbook SHA-256 changes during execution, the script records a `BLOCKER` and exits as a script failure condition.

## Corrected Governance Rules

- `tblCrosswalkCatalog` is governance metadata. It is not treated as a physical legacy-to-canonical crosswalk table.
- Physical crosswalk validation applies to tables on `19 - ID Crosswalks`, tables registered in `tblCrosswalkCatalog`, or table names ending in `IDCrosswalk`/`Crosswalk`, excluding `tblCrosswalkCatalog`.
- `tblCrosswalkCatalog` belongs on `15 LL_Catalog`; physical ID crosswalk tables belong on `19 - ID Crosswalks`.
- `DisplayOrder` in `tblLookupCatalogID` is validated within `LookupGroupID`, not globally across all groups.
- Boolean-like formulas are validated using cached displayed values from a `data_only=True` workbook load. Formula text itself is not treated as an invalid boolean.
- Formula-in-identifier findings are classified by field role: primary keys and crosswalk key formulas are errors, foreign-key and governance metadata ID formulas are warnings, and other ID-like formulas are informational.
- Formula reporting separates volatile formulas, compatibility-sensitive formulas, dynamic-array formulas, broken references, and external workbook references.

## Troubleshooting

- If `openpyxl` is missing, install it in the local virtual environment shown above.
- If the script exits `3`, check the console message and `migration_audit_report.json` if an output folder was created.
- If the workbook cannot be opened, confirm the path is quoted correctly in PowerShell and that the XLSX package is not corrupted.
- If many formula warnings appear, review `formula_audit.csv`; the script detects formula text and does not recalculate formulas.
- If readiness is `NOT READY`, review `migration_audit_findings.csv` for `BLOCKER` rows first.

## Read-Only Guarantee

The audit opens the workbook with:

```python
load_workbook(..., data_only=False, read_only=False)
```

It does not call `save()` on the source workbook and verifies the source SHA-256 hash before exit. The tool is intended for governance review before additional crosswalk population, lookup creation, or ID remediation.
