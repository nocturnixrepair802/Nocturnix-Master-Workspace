# Nocturnix Manufacturer Registry v0.1 Draft — QA

- Workbook SHA-256: `24A26319432D919C8D14B4B44377FB3826D7282657347D7283E90A73635412B9`
- Registry records: 35
- Alias records: 80
- Source observations: 780
- Identity conflicts: 25
- Review queue items: 25

## Checks
- **worksheet_order**: PASS — ['00 - Instructions', '01 - Manufacturer Registry', '02 - Alias Registry', '03 - Source Observations', '04 - Identity Conflicts', '05 - Review Queue', '06 - Validation Summary', '07 - Revision History', '08 - Import Metadata']
- **registry_count**: PASS — 35
- **registry_id_unique**: PASS — 35
- **legacy_code_unique**: PASS — 35
- **all_pending_verification**: PASS — 35
- **approval_fields_blank**: PASS — Evidence, verifier, and verification date blank
- **source_hashes_unchanged**: PASS — 9
- **production_blocked**: PASS — Production Authorization = Prohibited
- **placeholder_excluded**: PASS — MFR-LEGACY-001/N/A routed to conflict queue
- **tables_present**: PASS — {'00 - Instructions': 1, '01 - Manufacturer Registry': 1, '02 - Alias Registry': 1, '03 - Source Observations': 1, '04 - Identity Conflicts': 1, '05 - Review Queue': 1, '06 - Validation Summary': 1, '07 - Revision History': 1, '08 - Import Metadata': 1}
- **qa_read_only_hash**: PASS — 24A26319432D919C8D14B4B44377FB3826D7282657347D7283E90A73635412B9
