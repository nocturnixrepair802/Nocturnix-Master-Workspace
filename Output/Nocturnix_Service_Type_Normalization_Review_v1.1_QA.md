# Workbook QA Report

- Workbook: `D:\Business Portal\300_Pricing\Working\Nocturnix_Service_Type_Normalization_Review_v1.1.xlsx`
- Profile: Nocturnix Service Type Normalization Review
- Generated UTC: 2026-07-24T00:05:22.744830+00:00
- SHA-256: `b3d5804d1ef18942e9b1bc040ed88c5c5aead5b7021c9cde5368c42b40e3d1c4`
- Final status: **FAIL**
- Findings: 1 error(s), 3 warning(s), 0 informational

## Worksheet metrics

| Worksheet | Rows | Columns | Tables | Validations |
|---|---:|---:|---:|---:|
| 00 - Instructions | 265 | 12 | 1 | 7 |
| 01 - Canonical Service Types | 77 | 13 | 1 | 3 |
| 02 - Service Type Aliases | 17 | 13 | 1 | 5 |
| 03 - Service Normalization | 314 | 15 | 1 | 7 |
| 04 - Labor Normalization | 265 | 15 | 1 | 6 |
| 05 - Service Labor Candidates | 0 | 18 | 1 | 5 |
| 06 - Unresolved Review | 147 | 12 | 1 | 3 |
| 07 - Validation Summary | 8 | 3 | 1 | 0 |
| 08 - Revision History | 1 | 4 | 1 | 0 |
| 09 - Import Metadata | 20 | 2 | 1 | 0 |

## Configuration issues

None.

## Workbook issues

- **WARNING · TEXT_SURROUNDING_WHITESPACE** (00 - Instructions / L18): Text contains leading or trailing whitespace.
  - Value: `"'LGE '"`
  - Suggested action: Trim the value before import.
- **WARNING · USABILITY_FREEZE_PANES** (01 - Canonical Service Types): Freeze panes differ from the configured review layout.
  - Value: `{"expected": "A2", "actual": "A58"}`
- **ERROR · DATA_REQUIRED_BLANK** (03 - Service Normalization / B269): Required field is blank: Service Name
- **WARNING · USABILITY_FREEZE_PANES** (04 - Labor Normalization): Freeze panes differ from the configured review layout.
  - Value: `{"expected": "A2", "actual": "A163"}`

## Business-rule issues

None.

## Suggested improvements

- Trim the value before import.

## Final status: FAIL
