# Service Type Normalization Import Readiness Contract

Status: Proposed; requires governance approval before implementation

Contract version: 0.1

Prepared: 2026-07-23

Scope: Design only; no schema installation, import, activation, cutover, or source modification is authorized

## 1. Purpose and authority

This contract defines the gates between an approved review workbook and any future
database or runtime use of Service Type normalization data. Approval of a workbook
release establishes source integrity; it does **not** convert every row in that
workbook into production-approved data.

The sole approved source for the first shadow-import milestone is:

- Source workbook:
  `D:\Business Portal\300_Pricing\Approved\Nocturnix_Service_Type_Normalization_Approved_v1.0.xlsx`
- Approved version: `v1.0`
- Required SHA-256:
  `DE0F0957F687DF4866A2D06C4DF85A542FF58B61897481741EB1E6A04D825FBA`
- Workbook QA result: `PASS`

The release hash has been independently matched to the file named above. The
approved workbook is immutable input. No importer may save, repair, recalculate,
rename, move, or otherwise modify it.

This contract supplements ADR-012. Where a later approved ADR or status-transition
record conflicts with this proposal, the later explicit governance decision controls.
No implementation may infer approval from the workbook filename, release location,
QA result, confidence value, reviewer note, mapping method, or proposed identifier.

## 2. Safety invariant

The first import is a **shadow/reference import only**. It must not change pricing,
quoting, compatibility, repair selection, labor resolution, repair tickets, existing
runtime behavior, or any production workbook data.

The following stages are separate approvals and separate deployments:

1. **Schema installation** creates storage and constraints only. It imports no rows
   and changes no runtime read path.
2. **Shadow/reference import** copies eligible source and audit rows with runtime
   activation disabled.
3. **Runtime activation** makes individually approved rows eligible for a
   normalization read path behind an explicit feature/configuration gate.
4. **Legacy cutover** changes an authoritative runtime path or retires a legacy
   source. It requires its own migration, reconciliation, rollback, and business
   approval after a successful activation period.

Completion of one stage never authorizes the next.

## 3. Governing concepts

- **Release approval** means the workbook file and its review history were accepted
  as the approved evidence package.
- **Source row status** is the exact, case-sensitive status stored on the source row.
  It must be preserved without translation or trimming beyond validation.
- **Import eligibility** determines whether a row may be copied into shadow,
  reference, or audit storage.
- **Runtime eligibility** determines whether a copied row may affect behavior.
- **Imported status** records what the importer did with the row; it does not replace
  the source row status.
- **Effective date** is the instant from which an approved row is allowed to affect
  runtime. A null value means not effective.
- **Active** is a derived runtime state, never a synonym for “present in the
  database.”

For every behavior-bearing row:

```text
runtime_active =
    release_is_current
    AND source_row_status = "Approved"
    AND imported_status = "ACTIVATED"
    AND activation_approved = true
    AND effective_at IS NOT NULL
    AND effective_at <= evaluation_time
    AND (expires_at IS NULL OR evaluation_time < expires_at)
    AND superseded_version IS NULL
    AND exclusion_flag = false
```

Any missing, unknown, pending, unresolved, rejected, archived, superseded, or
conflicting condition evaluates to inactive.

## 4. Proposed status matrix

Status comparisons are exact and case-sensitive. The only recognized source statuses
for this release are those below.

| Exact source row status | Contract class | Shadow/reference import | Runtime activation | Required treatment |
| --- | --- | --- | --- | --- |
| `Approved` | Active/importable | Yes | Eligible, but only after a separate activation approval and effective date | Preserve status; activation remains off by default |
| `Archived` | Inactive/reference-only | Yes | Never | Preserve for lineage; exclude from active views |
| `Pending Review` | Blocked | Worksheet-dependent; reference/audit only | Never | Preserve; route to pending report |
| `Pending Service Review` | Blocked | Audit only unless a future worksheet policy permits reference storage | Never | Preserve; route to pending report |
| `Pending Labor Review` | Blocked | Reference/audit only | Never | Preserve; route to pending report |
| `Pending Evidence Review` | Blocked | Audit, or inactive mapping reference where permitted below | Never | Preserve; route to evidence queue |
| `Ready for Approval` | Blocked | Reference only | Never | Preserve; readiness is not approval |
| `Rejected` | Rejected/unresolved | Audit only; not a target mapping record | Never | Preserve rejection reason and reviewer evidence |
| `Unresolved` | Rejected/unresolved | Audit only; an inactive source-row snapshot may be retained for traceability | Never | Preserve ambiguity and required action |

An unrecognized, blank, differently cased, or whitespace-altered status is an import
failure, not a new status or a value to normalize automatically.

“Active/importable” in this matrix means *eligible to be activated later*. It does
not authorize activation during the shadow milestone.

## 5. Worksheet eligibility

| Worksheet | Required source rows | Shadow-import policy | Activation policy |
| --- | ---: | --- | --- |
| `00 - Instructions` | 265 table rows | Do not import as domain data. Capture controlled lists and policy metadata in the manifest/audit report. | Never |
| `01 - Canonical Service Types` | 77 | Import all 77 as inactive reference records even though all are `Pending Review`. | Only rows later changed to exact `Approved` by authorized governance, with an approved activation event |
| `02 - Service Type Aliases` | 17 | Import all 17 as inactive reference records; all are `Ready for Approval`. | Not eligible until exact `Approved`; never infer approval from rule type or confidence |
| `03 - Service Normalization` | 313 | Import all 313 as inactive source-to-canonical mapping references; all are `Pending Labor Review`. | Not eligible until exact `Approved` |
| `04 - Labor Normalization` | 265 | Import all as inactive references, including the two `Unresolved` rows, or store unresolved rows in the audit partition described below. No row enters an active lookup. | Only exact `Approved`; `Unresolved` is never active |
| `05 - Service Labor Candidates` | 0 | Require the worksheet/table and zero rows. Any row is a release/count mismatch for v1.0. | Never under this release |
| `06 - Unresolved Review` | 147 | Import all rows into audit/work-queue storage only, never into behavior-bearing mapping tables. | Never |
| `07 - Validation Summary` | 8 | Import or serialize as release-level reconciliation evidence only. | Never |
| `08 - Revision History` | 2 | Import as release audit history only. Its `Pending Review` values grant no domain approval. | Never |
| `09 - Import Metadata` | 26 | Import as immutable release metadata/evidence only. | Never |

### 5.1 Canonical reference exception

Canonical STY records may be imported before row-level approval **only** as inactive
reference records. This exception exists so foreign-key candidates, reviewer tools,
and reconciliation reports can resolve `STY######` identifiers without granting
runtime authority.

For these records:

- `source_review_status` remains `Pending Review`;
- `imported_status` is `SHADOW_REFERENCE`;
- `runtime_active` and `activation_approved` are false;
- `effective_at` is null;
- no default, warranty, tax, time, or other canonical field may override an existing
  runtime value;
- their identifiers must not be exposed through production selection lists or
  normalization APIs until activation is separately approved.

## 6. Status and evidence preservation

Aliases, Service ID mappings, and Labor Standard mappings must preserve:

- every source value exactly as represented in the workbook;
- the exact `Review Status`;
- reviewer, reviewer notes, evidence, confidence, method, ambiguity, and proposed
  target fields;
- source worksheet and a deterministic source row identifier;
- the release version and hash that supplied the row.

The importer may add derived classifications such as `BLOCKED` or
`SHADOW_REFERENCE`, but it must not overwrite, relabel, upgrade, or downgrade the
source status. Confidence and mapping method are evidence only. A high confidence,
an exact match, a populated proposed STY ID, or `Ready for Approval` cannot activate a
row.

If a later release changes a row status, that change is represented by a new
versioned row and an approval event. Historical status is never updated in place.

## 7. Proposed import manifest schema

The implementation should require a machine-readable manifest equivalent to:

```json
{
  "contract_version": "0.1",
  "import_mode": "SHADOW_REFERENCE",
  "source_workbook": "D:\\Business Portal\\300_Pricing\\Approved\\Nocturnix_Service_Type_Normalization_Approved_v1.0.xlsx",
  "approved_version": "v1.0",
  "source_sha256": "DE0F0957F687DF4866A2D06C4DF85A542FF58B61897481741EB1E6A04D825FBA",
  "expected_workbook_qa": "PASS",
  "worksheets": [
    {
      "name": "01 - Canonical Service Types",
      "table": "tblCanonicalServiceTypes",
      "expected_rows": 77,
      "key_fields": ["Proposed Canonical Service Type ID"],
      "status_field": "Review Status",
      "allowed_status_counts": {"Pending Review": 77},
      "import_target": "service_type_reference"
    }
  ],
  "expected_counts": {
    "canonical_service_types": 77,
    "aliases": 17,
    "service_normalization": 313,
    "labor_normalization": 265,
    "service_labor_candidates": 0,
    "unresolved_review": 147
  },
  "exclusions": [
    {
      "record_type": "Service Normalization",
      "source_record_id": "SVC000343",
      "domain_import": "EXCLUDED",
      "audit_presence_required": true,
      "reason": "Incomplete placeholder excluded from the 313-row Service Normalization population"
    }
  ],
  "activation_allowed": false,
  "legacy_cutover_allowed": false
}
```

The final manifest must also contain all ten worksheet/table names, exact column
schemas, expected status counts, workbook size and last-write metadata for
diagnostics, importer build/version, contract version, and a canonical digest of the
manifest itself. File timestamp and size are diagnostic only; SHA-256 is authoritative.

## 8. Proposed database table fields

Names are proposed and do not authorize schema creation.

### 8.1 `service_type_import_release`

| Field | Requirement |
| --- | --- |
| `import_release_id` | Immutable generated primary key |
| `contract_version` | Required |
| `source_workbook` | Required full source path |
| `approved_version` | Required; `v1.0` for the first milestone |
| `source_sha256` | Required uppercase 64-character SHA-256 |
| `manifest_sha256` | Required |
| `import_mode` | `SHADOW_REFERENCE`, `ACTIVATION`, or `ROLLBACK`; first milestone must be `SHADOW_REFERENCE` |
| `import_started_at_utc` / `imported_at_utc` | Required timestamps |
| `imported_by` | Required service/user identity |
| `importer_version` | Required |
| `imported_status` | `STARTED`, `VALIDATED`, `COMPLETED`, `FAILED`, `ROLLED_BACK`, or `SUPERSEDED` |
| `effective_at_utc` | Null for shadow import |
| `superseded_version` | Null unless this release has been superseded |
| `activation_allowed` | False for first milestone |
| `legacy_cutover_allowed` | False for first milestone |
| `reconciliation_report_uri` | Required on completion |
| `failure_report_uri` | Required on failure |

### 8.2 Common fields on every imported row

| Field | Requirement |
| --- | --- |
| `import_row_id` | Immutable generated primary key |
| `import_release_id` | Required foreign key to release |
| `entity_kind` | Canonical STY, alias, Service mapping, Labor mapping, unresolved item, or audit metadata |
| `entity_source_key` | Source business identifier where one exists |
| `source_workbook` | Required; denormalized for export/audit |
| `approved_version` | Required |
| `source_sha256` | Required |
| `source_worksheet` | Exact worksheet name |
| `source_table` | Exact Excel table name |
| `source_row_identifier` | Required deterministic identifier; see below |
| `source_row_number` | Physical Excel row, recorded for diagnostics but not used alone as identity |
| `source_review_status` | Exact source status, unmodified |
| `status_class` | Derived `ACTIVE_IMPORTABLE`, `INACTIVE_REFERENCE`, `BLOCKED`, or `REJECTED_UNRESOLVED` |
| `imported_at_utc` | Required |
| `imported_status` | `SHADOW_REFERENCE`, `AUDIT_ONLY`, `ACTIVATED`, `EXCLUDED`, `SUPERSEDED`, or `ROLLED_BACK` |
| `effective_at_utc` | Null unless separately activated |
| `expires_at_utc` | Optional |
| `superseded_version` | Version that superseded this row, otherwise null |
| `activation_approved` | False by default |
| `runtime_active` | Derived or constrained false unless all activation gates pass |
| `exclusion_flag` / `exclusion_reason` | Required for explicit exclusions |
| `source_row_sha256` | Digest of canonicalized source field names and values |
| `raw_payload` | Lossless structured snapshot of all source columns |
| `created_at_utc` | Required immutable audit timestamp |

`source_row_identifier` must be stable within a release:

- canonical: `01 - Canonical Service Types|<Proposed Canonical Service Type ID>`;
- alias: `02 - Service Type Aliases|<Alias ID>`;
- Service mapping: `03 - Service Normalization|<Service ID>`;
- Labor mapping: `04 - Labor Normalization|<Labor Standard ID>`;
- candidate: a documented composite key including Service ID and candidate identity;
- unresolved: `06 - Unresolved Review|<Record Type>|<Source Record ID>`;
- metadata/audit rows: worksheet name plus the worksheet's natural key, or a
  canonical row digest when no natural key exists.

### 8.3 Entity-specific fields

The normalized reference tables must retain all workbook columns in typed fields in
addition to `raw_payload`. At minimum:

- `service_type_reference`: proposed STY ID, category, type, description, applies-to,
  estimated minutes, default warranty days, taxable, source Active value, internal
  notes, identity authority, reviewer notes;
- `service_type_alias_reference`: alias ID, source system/field/value, normalized
  value, proposed STY ID/type, rule type, evidence, confidence, reviewer and notes;
- `service_normalization_reference`: Service ID/name, current Repair Type ID/value,
  Manufacturer ID/name, Device Family code/name, proposed STY ID/type, method,
  evidence, confidence, notes;
- `labor_normalization_reference`: Labor Standard ID, Legacy Labor ID/name, current
  Repair Type, Device Family code/name, Manufacturer ID/name, proposed STY ID/type,
  method, evidence, confidence, notes;
- `service_type_unresolved_audit`: record type, source ID/name, current type,
  candidate types/labor standards, ambiguity reason, missing evidence, required
  action, priority, notes.

The source `Active` column on canonical rows is evidence, not the database
`runtime_active` flag. Blank source Active values remain blank and must not default to
true.

## 9. Idempotency

1. The idempotency key is
   `(contract_version, approved_version, source_sha256, import_mode)`.
2. A completed import with the same key is a no-op after verification. It may produce
   a repeat-run report but may not insert duplicate releases or rows.
3. Row identity within a release is
   `(import_release_id, source_worksheet, source_row_identifier)`.
4. A repeated row with the same identity and `source_row_sha256` is unchanged.
5. The same identity with a different row digest under the same release hash is an
   internal integrity failure.
6. The same version with a different workbook hash is rejected. It requires a new
   approved version; a filename change is insufficient.
7. A new approved version inserts a new immutable release and new versioned rows. It
   does not update historical rows in place.
8. Import is transactional: release, rows, counts, and audit records commit together,
   or none become visible as a completed release.

## 10. Duplicate and conflict handling

- Duplicate natural keys within a worksheet are fatal.
- Duplicate `source_row_identifier` values are fatal.
- Duplicate STY IDs, alias IDs, Service IDs, or Labor Standard IDs within their
  governed worksheet are fatal.
- A proposed ID/type pair where only one side is populated, or where the type does
  not match the referenced canonical row, is fatal.
- The same source label mapping to multiple approved targets is a conflict and cannot
  activate. Pending alternatives may be retained as audit/reference evidence.
- Multiple aliases that normalize to the same value may be stored only if they have
  the same source scope and target or are explicitly marked blocked; an active target
  conflict is fatal.
- A Service or Labor mapping that references a missing STY record is fatal even in
  shadow mode.
- A row present in both active and exclusion sets is fatal.
- Cross-version changes are reported as added, removed, changed, status-changed, and
  target-changed. They are never silently merged.
- Database constraint errors, truncation, lossy type conversion, or non-round-tripping
  values abort the import.

No “first row wins,” fuzzy selection, automatic status promotion, or automatic
conflict resolution is allowed.

## 11. Explicit exclusion and audit handling for `SVC000343`

`SVC000343` is an incomplete placeholder removed from the approved 313-row Service
Normalization population. It must be handled as follows:

1. It must **not** appear in `service_normalization_reference`, active Service
   mappings, alias mappings, Labor mappings, or candidate mappings.
2. It must appear exactly once in `06 - Unresolved Review` for this release, with:
   `Record Type = Service Normalization`,
   `Source Record ID = SVC000343`,
   `Review Priority = High`, and
   `Review Status = Pending Evidence Review`.
3. Its unresolved source name, ambiguity, missing evidence, required action, and
   reviewer notes must be preserved exactly in audit storage.
4. The import manifest and reconciliation report must record it as an explicit
   exclusion, not a lost row.
5. Reconciliation must prove:
   `314 source Service records = 313 imported Service normalization references + 1 explicit exclusion`.
6. Any attempt to activate `SVC000343`, or its unexpected absence from the unresolved
   audit population, fails the import/activation gate.
7. A future reinstatement requires a new approved workbook version, a valid complete
   Service record, an explicitly approved row status, and removal/replacement of the
   exclusion through the authorized governance process. It may not be repaired during
   import.

## 12. Counts and reconciliation

The following v1.0 counts are exact:

| Population | Required count | Required status reconciliation |
| --- | ---: | --- |
| Canonical Service Types | 77 | 77 `Pending Review` |
| Service Type Aliases | 17 | 17 `Ready for Approval` |
| Service Normalization | 313 | 313 `Pending Labor Review` |
| Labor Normalization | 265 | 167 `Pending Evidence Review`; 11 `Pending Labor Review`; 85 `Pending Review`; 2 `Unresolved` |
| Service Labor Candidates | 0 | No rows |
| Unresolved Review | 147 | 147 `Pending Evidence Review` |

The import report must also reconcile 8 Validation Summary rows, 2 Revision History
rows, 26 Import Metadata rows, the controlled statuses in Instructions, and all ten
expected worksheets/tables in exact order.

Required equations include:

```text
read rows = inserted rows + unchanged idempotent rows + explicit audit-only rows
            + explicit exclusions

domain source rows = shadow/reference rows + explicit exclusions

active aliases + active service mappings + active labor mappings = 0
for the first shadow-import milestone
```

Counts alone are insufficient. The importer must compare natural-key sets, source-row
digests, status counts, foreign-key resolution, and a deterministic aggregate digest
per worksheet.

## 13. Activation and cutover rules

Activation must be a separate, auditable operation against an already reconciled
release. It may not reread the workbook and activate in one step.

Before a row can activate:

- its exact source status is `Approved`;
- the status transition was authorized under section 14;
- its release and row digests match the approved evidence;
- all referenced canonical and scoped parent rows are also active and effective;
- no unresolved or conflicting row has the same effective lookup key;
- an effective date has been approved;
- the activation batch lists the exact row identities and expected prior states;
- pre-activation tests and reports pass;
- rollback material is prepared and verified.

Aliases and mappings must be selected only from active views that enforce these
conditions. Raw/reference tables must not be queried directly by pricing, quoting,
compatibility, repair selection, labor resolution, or ticket workflows.

Legacy cutover additionally requires approved precedence rules, dual-run comparison,
business-owner sign-off, operational monitoring, a cutover window, and a tested
rollback. Shadow import or activation approval does not imply legacy cutover.

## 14. Approval authority and row-status changes

The following authority model is proposed and remains an open governance item until
named owners approve it:

- **Service taxonomy owner** approves canonical STY records and aliases.
- **Service catalog owner** approves Service ID-to-STY mappings.
- **Labor standards owner** approves Labor Standard-to-STY mappings and labor
  evidence.
- **Data governance/release owner** verifies provenance, conflict resolution, version
  creation, and manifest/reconciliation evidence.
- **Application/runtime owner** approves activation mechanics, feature gates,
  monitoring, and rollback.
- **Business process owner** approves legacy cutover and confirms no unintended
  pricing/quoting/repair effects.

No importer, developer, generator, or database administrator may change a source row
status as part of import.

A valid status change requires:

1. a recorded change request identifying row, old status, new status, evidence,
   decision, reviewer identity, approval timestamp, and effective date;
2. approval by the relevant domain owner and data governance owner;
3. resolution of linked unresolved-review items;
4. a newly versioned, immutable approved workbook and new SHA-256;
5. independent validation and reconciliation;
6. a new shadow import before any activation.

Direct database edits cannot confer source approval. Emergency deactivation may
disable an active row, but reactivation still requires the normal evidence and
approval path.

## 15. Rollback and re-import

- Shadow import rollback marks the import release `ROLLED_BACK` and removes it from
  current reference views. Immutable audit/release evidence remains retained.
- Activation rollback deactivates the exact activation batch and restores the prior
  active version/pointers atomically. It must not delete historical rows.
- Legacy cutover rollback restores the prior runtime read path/configuration and then
  deactivates the failed batch if required.
- Rollback must not write back to the approved workbook or production workbooks.
- Re-import of the same hash and mode is idempotent. A failed partial transaction
  must be cleaned or marked failed before retry and must never appear completed.
- Corrected content requires a new approved version and hash. Reusing `v1.0` for
  changed bytes is prohibited.
- Superseding a release sets release/row lineage to the new version; it does not
  mutate original provenance or source status.
- A rollback report must list affected release/batch IDs, row counts, prior and final
  active versions, timestamps, actor, reason, and validation results.

## 16. Import failure conditions

The importer must fail closed before committing if any of the following occurs:

- missing, unreadable, locked-for-unsafe-access, modified-during-read, corrupt, or
  macro/external-link-bearing source contrary to the approved workbook contract;
- SHA-256 mismatch, version mismatch, manifest mismatch, or reused version with
  different bytes;
- worksheet, table, order, header, defined-name, or required-column mismatch;
- any required count or status-count mismatch;
- unknown, blank, incorrectly cased, or normalized source status;
- missing or duplicate source identifier;
- broken canonical reference or inconsistent ID/type pair;
- duplicate, conflict, exclusion overlap, or lossy conversion;
- missing required provenance, imported timestamp, row digest, or audit payload;
- `SVC000343` present in Service Normalization, absent from required unresolved audit,
  duplicated, or eligible for activation;
- any Service-to-Labor candidate row in v1.0;
- any row marked active/effective during the shadow milestone;
- any write attempt to source or production workbooks;
- any detected runtime configuration, feature gate, schema, or data change outside
  the separately approved import target;
- inability to create a complete reconciliation/failure report;
- transaction or post-commit verification failure.

On failure, no release may be labeled completed and no row may be visible to runtime.

## 17. Required tests and reports before activation

### 17.1 Importer tests

- exact SHA/version/manifest acceptance and rejection cases;
- all status classifications, including unknown/blank/case-variant rejection;
- worksheet-specific eligibility and audit-only routing;
- canonical inactive-reference exception;
- zero-activation invariant for shadow import;
- idempotent repeat, interrupted import, retry, and same-version/different-hash cases;
- duplicate natural key, duplicate normalized alias, conflicting target, and broken
  reference cases;
- `SVC000343` exclusion, unresolved-audit presence, and 314 = 313 + 1 reconciliation;
- transaction rollback and post-commit digest verification;
- timestamp, effective-date, supersession, and activation-gate boundary cases;
- lossless round-trip comparison for every source column and null/blank distinction;
- negative integration tests proving current runtime repositories/services do not
  read the shadow tables.

### 17.2 Activation tests

- only exact `Approved` rows can enter active views;
- canonical parent activation is required before alias/mapping activation;
- pending, ready-for-approval, rejected, archived, and unresolved rows remain
  behaviorally invisible;
- conflicting active keys fail closed;
- effective start/end boundaries and supersession work deterministically in UTC;
- feature/configuration gate off means no behavior change;
- dual-run comparison shows no unapproved change to pricing, quoting, compatibility,
  repair selection, labor resolution, or repair tickets;
- activation rollback restores the exact previous behavior and active row set.

### 17.3 Required reports

1. Source integrity and manifest verification report.
2. Worksheet schema, count, key-set, status-count, and digest reconciliation report.
3. Per-row import disposition report:
   shadow reference, audit only, excluded, unchanged, or failed.
4. Duplicate/conflict and referential-integrity report.
5. `SVC000343` explicit exclusion report.
6. Provenance completeness and lossless round-trip report.
7. Shadow isolation report proving zero production/runtime consumers.
8. Activation candidate report listing only exact `Approved` rows and all required
   parent dependencies.
9. Negative-status report proving every non-approved row is inactive.
10. Runtime regression/dual-run report.
11. Rollback rehearsal report.
12. Signed approval record naming the release, hash, rows, effective date, approvers,
    feature gate, monitoring owner, and rollback owner.

## 18. Acceptance criteria: first shadow-import milestone

The first shadow-import milestone is accepted only when all of the following are true:

- the schema installation was separately approved and completed without changing
  runtime reads;
- the importer read only the approved v1.0 workbook and verified the required hash;
- all ten worksheets and expected tables/schemas were validated;
- all required counts and exact status distributions reconcile;
- 77 canonical rows are present only as inactive references;
- 17 aliases, 313 Service mappings, and 265 Labor mappings retain exact source
  statuses and are inactive;
- all 147 unresolved records are audit-only;
- there are zero Service-to-Labor candidates and zero active/effective normalization
  rows;
- `SVC000343` is excluded from Service mappings, appears exactly once in unresolved
  audit, and the 314 = 313 + 1 equation passes;
- every row contains required provenance, an immutable raw snapshot, and a row digest;
- a repeat import produces no duplicate release or row and no changed data;
- all duplicate, conflict, reference, status, and lossless round-trip checks pass;
- negative integration tests prove no current runtime code path consumes the imported
  data;
- no pricing, quoting, compatibility, repair selection, labor resolution, repair
  ticket, schema outside the approved shadow target, production data, generator, or
  workbook was changed;
- complete reconciliation and failure/rollback-ready reports are retained;
- governance and technical owners sign the shadow milestone without granting runtime
  activation or legacy cutover.

## 19. Open governance decisions requiring explicit approval

1. Confirm the exact production-approved row status. This proposal recognizes only
   `Approved`.
2. Name the individuals or roles for taxonomy, alias, Service mapping, Labor mapping,
   data governance, runtime activation, and legacy cutover authority.
3. Approve the canonical inactive-reference exception for all 77 `Pending Review`
   STY records.
4. Decide whether the two `Unresolved` Labor Normalization rows are duplicated into
   the inactive mapping-reference table plus audit storage, or stored only in audit
   storage. Either choice must keep them out of active views.
5. Approve the treatment of `Archived` rows as retained reference history rather than
   domain import targets.
6. Confirm whether `Rejected` and `Unresolved` require separate audit partitions or a
   common work/audit table with distinct status classes.
7. Define the stable owner and format of status-transition records and electronic
   sign-off evidence.
8. Define effective-date timezone/precision, backdating policy, expiration policy,
   and whether activation may be scheduled.
9. Approve cross-version supersession rules for partial row activation and rollback.
10. Define scoped alias uniqueness: global, source-system/field, device-family, and
    manufacturer scope precedence.
11. Define conflict precedence when more than one approved mapping could match the
    same runtime input. This contract defaults to fail closed.
12. Confirm whether canonical source fields such as estimated time, warranty, tax,
    and source Active may ever become runtime defaults; this phase prohibits it.
13. Approve retention periods and access controls for raw payloads, manifests,
    reports, failed imports, and rollback evidence.
14. Define the minimum dual-run period, monitoring thresholds, and business sign-off
    required before legacy cutover.
15. Approve a future workbook/status release process for resolving `SVC000343`; it
    remains explicitly excluded under v1.0.

Until these decisions and the relevant stage approvals are recorded, the only
permitted future implementation target described by this contract is an isolated,
inactive, read-only shadow/reference import.
