# Nocturnix Lookup Governance Standard v0.1 Draft

## 1. Purpose
Define draft governance rules for lookup domains.
## 2. Scope
Devices, Services, Parts, Labor, Compatibility, Pricing, Suppliers, and related systems.
## 3. Lookup domain ownership
Each lookup domain requires an assigned owner before approval.
## 4. Canonical ID requirements
Each lookup domain must have one canonical primary key.
## 5. ID prefix and format standards
IDs require documented, non-reused prefixes and formats.
## 6. Primary-key uniqueness
Primary keys must be unique and nonblank.
## 7. Foreign-key integrity
Operational tables must store IDs rather than repeated display labels; labels are resolved through lookup relationships.
## 8. Display-label standards
Labels must be clear, stable, and governed separately from IDs.
## 9. Duplicate-label handling
Duplicate labels require review and must not be merged automatically.
## 10. Alias handling
Aliases require traceable evidence and approval.
## 11. Active and inactive records
Inactive records remain retained for audit unless formally retired.
## 12. Sort-order rules
Sort order is display metadata, not identity.
## 13. Parent-child lookup relationships
Parent keys must resolve to governed parent records.
## 14. Crosswalk governance
New ID mappings require review and approval.
## 15. Duplicate review
Duplicate candidates must not be merged automatically.
## 16. Change-control requirements
All lookup changes require documented reason and evidence.
## 17. Approval requirements
No draft mapping is approved without separate authorization.
## 18. Database migration rules
The central lookup catalog is not production-authorized.
## 19. Production activation prohibition
Draft artifacts must not activate production use.
## 20. Versioning and SHA-256 requirements
Every artifact must be versioned and hashed.
## 21. Audit and evidence requirements
Source lineage, reviewer, and evidence fields must be retained.
## 22. Exceptions and escalation
Conflicts, blanks, invalid IDs, and unresolved dependencies require escalation.

IDs cannot be reused. Deleted IDs cannot be reassigned. The central lookup catalog is not production-authorized.
