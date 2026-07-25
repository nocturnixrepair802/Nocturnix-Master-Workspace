# Workbook QA Report

- Workbook: D:\Business Portal\100_Master_Data\Devices\Nocturnix_Device_Registry_v0.1_Draft.xlsx
- Profile: Nocturnix Device Registry v0.1 Draft
- Generated UTC: 2026-07-24T05:19:42+00:00
- Source SHA-256: {
  "Nocturnix_Manufacturer_Registry_v0.1_Draft.xlsx": "24a26319432d919c8d14b4b44377fb3826d7282657347d7283e90a73635412b9",
  "Nocturnix_Master_Devices_Catalog_v1.xlsx": "23840312b08a55031021e73aed6ea8835ddccbe215b8bf133751b64fd44aad96",
  "Nocturnix_Master_Parts_Catalog_v1.xlsx": "3f6387b43647aa63c69f2995fbc0c272d9f85c0dd1a340ebaab842704d3c3464",
  "Nocturnix_Master_Services_Catalog_v1.xlsx": "f1a85069f3f7655e2fd375cf2ee63c5c716422e1a7d2befe61073005396e34c2",
  "Nocturnix_Master_Compatibility_Catalog_v1.xlsx": "58442236fa3587eb29e86f70ac5439e5cba9681feb26b7c1848c290e9287baf4"
}
- Workbook SHA-256 before QA: b43dd38c8897e3665605f039591a0cfffd3554fa1f3144a242a0ffd7971d9d9a
- Workbook SHA-256 after QA: b43dd38c8897e3665605f039591a0cfffd3554fa1f3144a242a0ffd7971d9d9a
- Final status: **WARN**
- Findings: Unique Device IDs: PASS, Manufacturer References: WARN, Duplicate Device Detection: PASS, Alias Consistency: WARN, Required Fields: PASS, Worksheet Integrity: PASS, Governance Gates: PASS

## Validation summary

| Validation | Status | Details |
|---|---|---|
| Unique Device IDs | PASS | All generated Device IDs are unique. |
| Manufacturer References | WARN | Some devices remain unresolved against the canonical manufacturer registry. |
| Duplicate Device Detection | PASS | No duplicate device records were detected. |
| Alias Consistency | WARN | Alias records were preserved as observations only and remain pending verification. |
| Required Fields | PASS | The required registry fields are present for every device row. |
| Worksheet Integrity | PASS | All required worksheets are present with headers. |
| Governance Gates | PASS | Governance status remains pending verification and no production flags are enabled. |

## Governance blockers
- Canonical manufacturer mappings remain unresolved for observed manufacturer values that do not exist in the approved manufacturer registry.
- Identity conflicts were preserved as pending verification rather than approved.

## Unresolved conflicts
- DEV000001: iPhone -> 
- DEV000002: iPhone -> 
- DEV000003: iPhone -> 
- DEV000004: iPhone -> 
- DEV000005: iPhone -> 
- DEV000006: iPhone -> 
- DEV000007: iPhone -> 
- DEV000008: iPhone -> 
- DEV000009: iPhone -> 
- DEV000010: iPhone -> 
- DEV000011: Galaxy -> 
- DEV000012: Galaxy -> 
- DEV000013: Galaxy -> 
- DEV000014: Galaxy -> 
- DEV000015: Galaxy -> 
- DEV000016: Galaxy -> 
- DEV000017: Galaxy -> 
- DEV000018: Galaxy -> 
- DEV000019: Galaxy -> 
- DEV000020: Galaxy -> 
- DEV000021: Galaxy -> 
- DEV000022: Galaxy -> 
- DEV000023: Galaxy -> 
- DEV000025: Galaxy -> 
- DEV000029: Maxwest -> 
- DEV000030: TCL -> 
- DEV000039: N/A -> 
- DEV000040: N/A -> 
- DEV000041: N/A -> 
- DEV000042: N/A -> 
- DEV000043: N/A -> 
- DEV000044: N/A -> 
- DEV000045: N/A -> 
- DEV000046: N/A -> 
