# Service Type Normalization Validation Rules

## Independent validator

`Scripts/validate_service_type_normalization_review.py` does not call or import
the generator. It reopens the published OOXML artifact and reads all protected
sources independently.

## Structure and OOXML

The validator requires:

- the exact ten worksheets in exact order;
- unique worksheet names of 31 characters or fewer;
- exactly one expected Excel Table on each worksheet;
- exact schemas for the six governed data/review tables;
- frozen table headers;
- a valid, non-corrupt OOXML ZIP package;
- no VBA project and no external links;
- no stale transactional temporary output.

## Canonical taxonomy and identity

- Detailed headers must be row 4, columns L-T, with the documented names.
- Every populated detailed Service Type is preserved exactly.
- Artifact row count must equal the runtime canonical source count.
- The confirmed 70-row baseline is enforced unless runtime source count changed
  and the changed count is recorded in metadata.
- Proposed IDs match `^STY\d{6}$`, are nonblank, and are unique.
- Proposed canonical ID/type references must resolve to the snapshot.

## Source preservation and coverage

- Service normalization has one row per runtime Master Service record; the
  confirmed baseline is 314.
- Labor normalization has one row per runtime Master Labor record; the
  confirmed baseline is 265.
- Source Service identity, names, Repair Type, Manufacturer, and Device Family
  values equal the protected source in source order.
- Source Labor governed/legacy identity, name, Repair Type, Device Family, and
  Manufacturer values equal the protected source in source order.
- Runtime count changes must be recorded in metadata.

## Aliases and normalization

- Alias IDs match `^STA\d{6}$` and are unique.
- Alias Rule Type, Mapping Method, Confidence, and Review Status values belong
  to their governed lists.
- Proposed canonical ID/type pairs are both blank or both populated and
  consistent.
- Every generated canonical, alias, normalization, candidate, and unresolved
  status is `Pending Review`; any generated `Approved` status fails validation.

## Labor candidate constraints

- Candidate Service IDs resolve to Service normalization.
- Candidate canonical Service Type equals the Service proposal.
- A populated suggested Labor Standard resolves to Labor normalization.
- Suggested Labor and Service canonical Service Type IDs are equal.
- Labor Device Family equals Service family code/name or is explicitly
  universal.
- A populated Labor Manufacturer equals Service manufacturer ID/name.
- `Ambiguity Count > 1` requires a blank Suggested Labor Standard ID.
- `Ambiguity Count == 1` requires the unique governed Labor Standard ID.

## Defined names and time safety

- Exactly the ten documented defined names exist.
- Each name resolves to its documented single-column range beginning on row 2.
- Every data validation is a list whose formula is only `=<defined_name>`.
- Direct cross-sheet formulas are rejected.
- Persisted datetime values must be timezone-naive UTC-compatible Excel values.

## Protected-state hashes

Generation-time SHA-256 or `ABSENT` state is stored for:

- `Nocturnix_Master_Database.xlsm`
- `Nocturnix_Master_Services_Catalog_v1.xlsx`
- `Nocturnix_Master_Labor_Catalog_v1.xlsx`
- `Labor_Mapping_Review_v1.xlsx`

The independent validator compares current protected state to recorded state.
Any difference fails validation. Neither script saves a protected workbook.

## Authorized commands for this task

Only these static checks are authorized:

```powershell
python -m py_compile `
  Scripts/generate_service_type_normalization_review.py `
  Scripts/validate_service_type_normalization_review.py

ruff check `
  Scripts/generate_service_type_normalization_review.py `
  Scripts/validate_service_type_normalization_review.py

git diff --check
```

Do not run either workflow during code/documentation review.
