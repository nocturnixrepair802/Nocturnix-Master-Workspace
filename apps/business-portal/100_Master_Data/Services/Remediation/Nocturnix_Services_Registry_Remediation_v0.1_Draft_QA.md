# Nocturnix Services Registry Remediation v0.1 Draft - QA

- Workbook: D:/Business Portal/100_Master_Data/Services/Remediation/Nocturnix_Services_Registry_Remediation_v0.1_Draft.xlsx
- Workbook SHA-256 before QA: 3A4CF9ABE3BD954D93C50094AB08D53ADB64FAE143AFC7AB7DBD312245B15EF7
- Workbook SHA-256 after QA: 3A4CF9ABE3BD954D93C50094AB08D53ADB64FAE143AFC7AB7DBD312245B15EF7
- Sources and existing registries unchanged: true
- Final status: WARN

## Counts
- exactManufacturerCandidates: 0
- ambiguousManufacturerCandidates: 0
- unresolvedManufacturerObservations: 314
- exactDeviceApplicabilityCandidates: 0
- ambiguousDeviceApplicabilityCandidates: 0
- exactPartRequirementCandidates: 0
- ambiguousPartRequirementCandidates: 0
- exactLaborReferenceCandidates: 0
- ambiguousLaborReferenceCandidates: 0
- unsupportedRelationships: 314
- duplicateGroupsReviewed: 15
- identityConflicts: 314
- reviewItems: 314

## Validation
- **Referenced Service IDs Exist**: PASS - All generated evidence rows use Services Registry IDs.
- **Referenced Manufacturer IDs Exist**: PASS - Exact manufacturer candidates are restricted to Manufacturer Registry IDs.
- **Referenced Device IDs Exist**: PASS - Exact device candidates are restricted to Device Registry IDs.
- **Referenced Part IDs Exist**: PASS - Exact part candidates are restricted to Parts Registry IDs.
- **Source Traceability**: PASS - Mapping rows include source workbook, worksheet, and record where source-supported.
- **Exact/Ambiguous Separation**: PASS - Candidate worksheets are separated by match strength.
- **Unsupported Not Promoted**: PASS - 314 unsupported relationship observations retained separately.
- **Approval Fields Blank**: PASS - Governance status remains Pending Verification; no approval fields populated.
- **Source Workbooks Unchanged**: PASS - Verified by before/after SHA-256.
- **Existing Services Registry Hash Unchanged**: PASS - Verified by before/after SHA-256.
- **Output Workbook QA Hash Stable**: PASS - Before QA 3A4CF9ABE3BD954D93C50094AB08D53ADB64FAE143AFC7AB7DBD312245B15EF7; after QA 3A4CF9ABE3BD954D93C50094AB08D53ADB64FAE143AFC7AB7DBD312245B15EF7.
