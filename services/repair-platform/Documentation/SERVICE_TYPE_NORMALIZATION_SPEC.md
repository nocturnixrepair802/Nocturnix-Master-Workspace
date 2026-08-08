# Service Type Normalization and Labor Mapping Specification

## Purpose and authority

Version 1.0.2 creates a standalone review package that relates Master Services,
the detailed canonical Service Type vocabulary, Device Family, optional
Manufacturer, and Master Labor. It does not alter or import into a protected
workbook.

The detailed taxonomy on canonical worksheet `33 Service Types`, row 4 and
columns L-T, is authoritative for review. The B-H summary taxonomy is retained
only as legacy/reference context.

Service Type describes the governed operation. Service Name is the
device/model-specific commercial label. Labor Standard is the separate
definition of expected time, skill, and work.

## Protected inputs and output

The generator reads:

- `Data/Nocturnix_Master_Database.xlsm`
- `D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Services_Catalog_v1.xlsx`
- `D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Labor_Catalog_v1.xlsx`
- `D:\Business Portal\300_Pricing\Working\Labor_Mapping_Review_v1.xlsx`, when
  present

It writes only:

`D:\Business Portal\300_Pricing\Working\Nocturnix_Service_Type_Normalization_Review_v1.xlsx`

The output is saved first to a temporary sibling, reopened and checked, then
published atomically. Protected inputs are hashed before and after generation.
An absent optional protected file is recorded as `ABSENT` and must remain
absent.

## Identity policy

The generator scans explicit `Service Type ID` columns in the canonical
workbook. Populated IDs must match `^STY\d{6}$`, be unique, and cover every
detailed Service Type. An incomplete governed namespace blocks generation.

When there is no populated governed namespace, ADR-012 authorizes review-local
IDs beginning with `STY000001` in detailed taxonomy order. These IDs identify
review records only and do not authorize canonical import.

## Exact workbook contract

| Order | Worksheet | Excel Table |
| ---: | --- | --- |
| 1 | 00 - Instructions | `tblSTNInstructions` |
| 2 | 01 - Canonical Service Types | `tblCanonicalServiceTypes` |
| 3 | 02 - Service Type Aliases | `tblServiceTypeAliases` |
| 4 | 03 - Service Normalization | `tblServiceNormalization` |
| 5 | 04 - Labor Normalization | `tblLaborNormalization` |
| 6 | 05 - Service Labor Candidates | `tblServiceLaborCandidates` |
| 7 | 06 - Unresolved Review | `tblSTNUnresolvedReview` |
| 8 | 07 - Validation Summary | `tblSTNValidationSummary` |
| 9 | 08 - Revision History | `tblSTNRevisionHistory` |
| 10 | 09 - Import Metadata | `tblSTNImportMetadata` |

Names are unique, no longer than 31 characters, and every worksheet has exactly
one Excel Table.

## Canonical snapshot

The snapshot preserves:

- Service Category
- Service Type
- Service Description
- Applies To
- Estimated Time (Min)
- Default Warranty (Days)
- Taxable
- Active
- Internal Notes

It adds proposed identity authority, `Pending Review`, and reviewer notes.

## Mapping policy

Normalized text is used for case-insensitive exact comparison only. It is not a
similarity score. Exact canonical Repair Type matches may be proposed with high
confidence and remain pending.

The initial alias register contains the explicit ADR-012 candidates. Single
targets may populate a proposed canonical pair. Ambiguous, missing, and
new-type-required cases remain blank and are routed to unresolved review.

`Miscellaneous Repair` is never mapped from its broad label. A small,
documented set of required-token rules may produce a low-confidence candidate
from Service Name. Zero or multiple rule matches remain unresolved.

## Labor relationship policy

A relationship candidate exists only when:

1. Service and Labor proposed canonical Service Type IDs are equal.
2. Labor Device Family equals the Service family code/name, or the Labor row is
   explicitly `All`, `All Devices`, `Any`, or `Universal`.
3. A populated Labor Manufacturer equals the Service manufacturer ID/name.

Exactly one eligible Labor Standard may populate `Suggested Labor Standard ID`.
When multiple standards remain eligible, the suggestion and labor detail fields
stay blank, `Ambiguity Count` records the count, evidence lists the governed
Labor Standard IDs, and unresolved review receives the relationship.

No generated mapping is approved.

## Runtime count policy

The confirmed baseline is 70 detailed Service Types, 314 Services, and 265
Labor Standards. Runtime source counts are recorded in validation and metadata.
A changed runtime count is visible as `Runtime Source Changed`; the independent
validator requires the artifact count to match the current protected source.

## Non-goals

Version 1.0.2 does not:

- write to Master Services, Master Labor, or the canonical workbook;
- import aliases or mappings;
- infer approval from fuzzy similarity;
- change the existing Services or Labor generators/validators;
- approve a Service Type, alias, Labor Standard, or relationship;
- determine customer price, cost, inventory, payroll, or scheduling.
