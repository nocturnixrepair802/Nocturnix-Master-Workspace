# Master Services Catalog v1 Specification

## Purpose

Define a standalone, proposed canonical Master Services catalog for review before
any separately approved import into `Data/Nocturnix_Master_Database.xlsm`.

## Scope

The package contains 314 retained legacy Repair records, proposed `SVC######`
identities, lookup tables, conservative labor mappings, legacy pricing
observations, validation results, revision history, and import metadata. It does
not calculate prices or costs and does not modify an authoritative workbook.

## Source Precedence

1. `Documentation/MASTER_CATALOG_ARCHITECTURE.md` defines canonical ownership and
   architectural boundaries.
2. `Documentation/ADR/ADR-006-canonical-master-catalog-baseline.md` establishes
   that architecture as authoritative.
3. The deduplication proposal's `01 - Retained` sheet supplies reviewed legacy
   Repair candidates and source provenance.
4. The labor catalog supplies labor standards, tiers, difficulty, skill, and
   warranty reference data.
5. The canonical database supplies existing lookup identities. It is read-only.
6. Legacy values are preserved as source observations and never override an
   authoritative canonical value without review.

## Service Identity Rules

- Read all existing Service IDs from `Nocturnix_Master_Database.xlsx`, worksheet
  `34 Master Services`, at runtime.
- Accept existing IDs for sequence calculation only when they match
  `^SVC\d{6}$`; report malformed values and exclude them from the calculation.
- Assign new IDs in ascending Source Record Number order using the next number
  after the highest valid existing ID.
- Never reuse or renumber an existing Service ID and never guess a start value
  when the authoritative worksheet cannot be read.
- The current confirmed highest existing ID is `SVC000075`, so the expected
  314-row draft range is `SVC000076` through `SVC000389`. This is a review
  baseline, not a hard-coded permanent start.
- Service IDs are unique and nonblank in the output artifact.
- `Legacy Service SKU` is an alias/reference and never the canonical key.
- Preserve the legacy SKU and source record number exactly.
- Do not create a service for a rejected, archived, or duplicate-exclusion row.
- Distinct reviewed services sharing a legacy SKU receive distinct Service IDs.
- Unresolved conflicts remain `Draft` and `Pending Review`.

## Labor Mapping Rules

Labor matching uses Device Category, Manufacturer, Device Scope, Service, Repair
Difficulty, and Skill Level. The generator derives a device category from legacy
type/group/name text, compares service descriptions to labor service names, and
uses manufacturer agreement as supporting evidence. A match is accepted only
when its score clears the documented threshold and is not materially tied with a
different labor record.

When a reliable match exists, the generator copies Labor Standard ID, Standard,
Minimum, and Maximum Minutes, Labor Tier, Repair Difficulty, and Skill Level.
When evidence is insufficient, Labor Standard ID and time fields remain blank,
the service is preserved, and Review Status becomes `Pending Labor Mapping`.
The generator never invents a labor duration.

## Pricing Deferral Rules

`Legacy Retail Price` and `Legacy Cost` are preserved observations only. They are
not approved prices, final costs, pricing inputs, or calculated outputs.

- Price greater than zero: `Legacy Price Review`.
- Price equal to zero: `Pending Pricing Review`.
- Invalid or unavailable observations: `Pending Pricing Review`.
- No final customer price or final cost column is permitted.
- Pricing approval waits for the separately governed Master Pricing Model.

## Conflict Handling

The generator reads reviewed conflict rows from the proposal. Approved decisions
are preserved as reviewer context. An unresolved conflict is not merged or
discarded; its service remains `Draft` with `Pending Review`. Legacy values are
never overwritten. Canonical identity changes occur only in this proposed output.

## Ownership

- Service taxonomy and repair definitions: Repair Engineering.
- Labor standards and mappings: Operations and Labor Planning.
- Pricing status and future pricing model: Pricing Governance.
- Manufacturer and device taxonomy: Product Catalog and Sourcing.
- Workbook schema, validation, and version metadata: Data Engineering.
- Draft preparation owner: Tamara Grandoit.

## Review Workflow

1. Validate the generated workbook independently.
2. Review unresolved SKU conflicts and lookup gaps.
3. Review all `Pending Labor Mapping` services.
4. Review legacy pricing observations without approving final pricing.
5. Confirm service flags, warranty, and turnaround values.
6. Approve or reject proposed service identities.
7. Plan a separate canonical import only after explicit authorization.

## Import Boundary

Generation and validation do not import data. The output workbook is a review
artifact. Any canonical database update requires a separate approved migration,
backup, validation run, ownership sign-off, and rollback plan. PricingEngine and
QuoteEngine are outside this package's scope.
