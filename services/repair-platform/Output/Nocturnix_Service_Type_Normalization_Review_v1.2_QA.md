# Workbook QA Report

- Workbook: `D:\Business Portal\300_Pricing\Working\Nocturnix_Service_Type_Normalization_Review_v1.2.xlsx`
- Profile: Nocturnix Service Type Normalization Review
- Generated UTC: 2026-07-24T00:16:13.037891+00:00
- SHA-256: `ca1497e347852b74ef87b4d23baf0eecc92dd29c34ef99818048e0728d778b87`
- Final status: **FAIL**
- Findings: 1 error(s), 2 warning(s), 0 informational

## Worksheet metrics

| Worksheet | Rows | Columns | Tables | Validations |
|---|---:|---:|---:|---:|
| 00 - Instructions | 265 | 12 | 1 | 7 |
| 01 - Canonical Service Types | 77 | 13 | 1 | 3 |
| 02 - Service Type Aliases | 17 | 13 | 1 | 5 |
| 03 - Service Normalization | 313 | 15 | 1 | 7 |
| 04 - Labor Normalization | 265 | 15 | 1 | 6 |
| 05 - Service Labor Candidates | 0 | 18 | 1 | 5 |
| 06 - Unresolved Review | 147 | 12 | 1 | 3 |
| 07 - Validation Summary | 8 | 3 | 1 | 0 |
| 08 - Revision History | 1 | 4 | 1 | 0 |
| 09 - Import Metadata | 20 | 2 | 1 | 0 |

## Configuration issues

None.

## Workbook issues

- **WARNING · USABILITY_FREEZE_PANES** (00 - Instructions): Freeze panes differ from the configured review layout.
  - Value: `{"expected": "A2", "actual": "A6"}`
- **WARNING · USABILITY_FREEZE_PANES** (03 - Service Normalization): Freeze panes differ from the configured review layout.
  - Value: `{"expected": "A2", "actual": "A254"}`
- **ERROR · DATA_ROW_COUNT** (03 - Service Normalization): Populated data-row count differs from the configured contract.
  - Value: `{"expected": 314, "actual": 313}`

## Business-rule issues

None.

## Suggested improvements

None.

## Final status: FAIL
