# Legacy Catalog Deduplication Proposal Review Guide

## Purpose and Scope

Use this guide to review
`Nocturnix_Legacy_Catalog_Deduplication_Proposal_v1.xlsx`. The workbook is a
proposal and review artifact only. It is not a production import, and approval
of a workbook row does not itself update a canonical catalog.

Reviewers must preserve source provenance, retain original legacy values, and
record decisions in `09 - Decision Log`. Do not assign final canonical IDs or
begin a canonical import during this review.

## Proposal Baseline

The proposal contains:

- 428 retained rows.
- 315 proposed exact-duplicate exclusions.
- 15 conflicting SKU records requiring manual review.
- 1,110 unresolved issue instances.

Issue instances are not unique records. One retained record can appear in
several review categories, such as a SKU conflict, a manufacturer gap, and a
zero-value issue. Do not add the issue counts together to determine the number
of affected records; use the workbook's unique unresolved-row metric for that
purpose.

## Review Order

Complete the review in this order:

1. Review SKU conflicts in `03 - SKU Conflicts`.
2. Resolve manufacturer gaps in `06 - Manufacturer Review`.
3. Resolve supplier gaps for physical items in `07 - Supplier Review`.
4. Review monetary classifications in `05 - Zero Value Review`.
5. Approve primary and secondary destinations in `08 - Destinations`.
6. Approve proposed exclusions in `02 - Duplicate Exclusions`.

Record material decisions, supporting reasons, reviewer identity, and decision
date in `09 - Decision Log`. Leave a decision pending when the available
evidence is insufficient.

## SKU Conflict Decision Rules

For each conflict group in `03 - SKU Conflicts`, compare all rows in the group
before deciding. Select one of these outcomes:

- **Keep both with new canonical IDs:** Use when the records represent distinct
  catalog items despite sharing a legacy SKU. Canonical IDs are assigned only
  in a later controlled process, not in this proposal workbook.
- **Retain one and archive one:** Use when one record is the valid catalog item
  and the other is obsolete, superseded, or erroneous. Document why the chosen
  record is authoritative.
- **Correct an incorrect legacy SKU:** Use when reliable source evidence shows
  that a legacy SKU was entered incorrectly. Preserve the original SKU as
  provenance and record the proposed correction in the decision log.
- **Identify a true variant:** Use when the rows describe legitimate variants,
  such as different models, configurations, conditions, or compatible items.
  Document the distinguishing fields required by the future canonical records.
- **Escalate for manual research:** Use when the workbook does not contain enough
  evidence to distinguish the records. Do not merge, archive, or correct a row
  based on assumption alone.

Never promote a legacy SKU directly to a canonical primary key. Keep all 15
conflicting records retained and pending until an explicit decision is
documented.

## Manufacturer Review Rules

- Infer a manufacturer only when the device or item name clearly and
  unambiguously identifies it.
- Leave the proposed manufacturer pending when the name, type, or other legacy
  evidence could support more than one manufacturer.
- Preserve the original legacy manufacturer value, including a blank value, as
  source provenance. Enter any recommendation in the proposal field rather
  than overwriting the legacy field.
- Escalate ambiguous, abbreviated, or house-brand descriptions for research.

## Supplier Review Rules

- A supplier is required only for physical categories: Part, Device, Tool, and
  Accessory.
- Repair services do not require a supplier. Do not flag a Repair record solely
  because its supplier is blank.
- An unknown supplier may remain unresolved during the initial migration when
  no reliable evidence is available.
- Do not invent, infer casually, or assign a preferred supplier merely to fill
  a blank field.
- Preserve the original legacy supplier value and record any proposed mapping
  separately.

## Zero-Value Review Rules

Review each record's business meaning, not only its numeric classification:

- **Price = 0 and Cost = 0:** Determine whether the record is a valid non-priced
  reference, an inactive/archive candidate, or a record with missing business
  data. Do not assume that both zeros mean the record is invalid.
- **Price > 0 and Cost = 0:** Confirm whether cost is intentionally unavailable
  or whether cost data is missing. A valid sale price does not prove that zero
  cost is correct.
- **Price = 0 and Cost > 0:** Confirm whether the item is internal-use,
  non-sellable, bundled, awaiting pricing, or missing retail-price data. Do not
  publish it as a zero-price sale item without approval.
- **Valid non-priced reference:** Retain only when the record has a documented
  operational purpose and is not intended to carry a direct price.
- **Inactive/archive candidate:** Use when evidence shows the record should be
  preserved for history but excluded from active catalog use.
- **Missing business data:** Use when price or cost should exist but cannot be
  established from the available legacy sources. Leave the value unresolved
  and identify the required follow-up.

Do not automatically convert zero values to blanks, copy price into cost, copy
cost into price, or invent replacement values.

## Destination Approval Rules

In `08 - Destinations`, confirm that the primary destination matches the record
category:

- Repair to `master_services staging`.
- Part to `parts_catalog staging`.
- Device to `master_devices staging`.
- Tool to `tool_catalog staging`.
- Accessory to `accessories_catalog staging`.

Review `inventory_items staging` and `pricing staging` only as secondary
destination indicators. A secondary indicator does not replace the primary
destination and does not authorize an import. Leave unsupported or ambiguous
destinations pending and document the required correction.

## Duplicate-Exclusion Approval Rules

Review `02 - Duplicate Exclusions` only after conflicts, enrichment issues, and
destinations have been assessed. For each exact-duplicate group:

- Confirm that the excluded row is an exact duplicate of the cited retained
  source row.
- Confirm that source-row provenance and the legacy SKU agree.
- Approve only the excess copy; do not approve deletion or modification of the
  raw source workbook.
- Leave the exclusion pending if any material field differs or the retained
  representative is questionable.
- Record exceptions and reversals in `09 - Decision Log`.

The 315 rows are proposed exclusions from a future cleaned catalog, not source
deletions.

## Recommended Staged Review Target

### First Pass: SKU Conflicts

Resolve or explicitly escalate all 15 conflicting records. These decisions can
change identity, variant, and destination conclusions, so they should precede
bulk enrichment work.

### Second Pass: High-Value Repair and Part Records

Prioritize Repair and Part records with the highest price or cost exposure.
Confirm identity, manufacturer, monetary interpretation, and destination before
reviewing lower-impact records.

### Third Pass: Remaining Lookup Enrichment

Work through the remaining manufacturer, physical-item supplier, category,
type, monetary, and other lookup-reconciliation issues. Preserve unresolved
items as pending rather than making unsupported assignments.

### Final Pass: Exclusions and Destinations

Complete duplicate-exclusion approval and destination approval after upstream
identity and enrichment decisions are stable. Reconcile the final decision log
to the workbook validation summary before authorizing any separate import
planning activity.
