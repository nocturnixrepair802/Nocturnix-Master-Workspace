# Engine Refactor Plan

Last updated: 2026-07-22
Status: Proposed
Scope: Engines, their repository contracts, `RepairManager`, and relevant workbook
schemas

## Objective

Restore the quote, pricing, inventory, and compatibility contracts with minimal
disruption. The migration should first make current behavior explicit and testable,
then introduce canonical workbook schemas and cleaner repository/engine boundaries.

No phase should combine workbook schema migration with unrelated GUI or workflow
refactoring.

## Current dependency path

```text
Application
  -> RepairManager
       -> QuoteEngine
            -> CompatibilityEngine
            -> PricingEngine
       -> PricingEngine
       -> InventoryEngine
       -> CompatibilityEngine
```

All current engines receive the shared `dict[str, pandas.DataFrame]` and query tables
directly. `QuoteEngine` constructs additional pricing and compatibility engines,
duplicating the instances already owned by `RepairManager`.

## Workbook schema versus engine expectations

### Compatibility

Database key: `compatibility`

| Engine expectation | Current workbook column | Status | Resolution |
|---|---|---|---|
| `Device Family` | `Device Family` | Match | Retain initially; rename to `Device Family Code` in the canonical schema. |
| `Service ID` | `Service Name` | Mismatch | Rename workbook column to `Service ID`; current values are IDs such as `SVC000038`, not names. |
| `Supported` | `Supported` | Match but unused by engine | Engine must evaluate the stored Boolean instead of treating every matching row as supported. |
| Reason text | `Notes` | Available but unused | Use notes when present; otherwise provide a standard reason. |
| Required capability | `Requires Capability` | Available but unused | Include in the compatibility result and enforce through the workflow when applicable. |

Confirmed failure: `CompatibilityEngine.validate()` indexes the absent `Service ID`
column and raises `KeyError`.

### Inventory

Database key currently used: `parts_catalog`

| Engine expectation | Current workbook column | Status | Resolution |
|---|---|---|---|
| `SKU` | `SKU` | Match | Retain as the inventory lookup identifier. |
| `Quantity` | No corresponding column | Missing | Do not overload the current catalog. Add a dedicated inventory table with quantity-on-hand. |

The current `parts_catalog` contains catalog/export fields:

```text
Manufacturer, Device Type, Device Family, Device Model, Service Type,
Labor, Parts, Final Price, Square Item Name, SKU
```

It is not an inventory ledger. `InventoryEngine.available()` returns `False` for an
unknown SKU but raises `KeyError: 'Quantity'` if a matching row reaches the quantity
lookup. `InventoryRepository.in_stock()` has the same broken assumption.

### Pricing

Database keys: `labor_rates` and `retail_pricing`

| Engine expectation | Current workbook column | Status | Resolution |
|---|---|---|---|
| `labor_rates.Hourly Rate` | `labor_rates.Labor Price` | Mismatch | Decide whether the value is hourly or a fixed service charge; canonical schema uses `Hourly Rate`. |
| Service/rate selector | `labor_rates.Service Type` | Present but ignored | Require an explicit `Service ID` or service-rate identifier instead of reading row zero. |
| Labor duration | `labor_rates.Estimated Time` and `master_services.Estimated Labor (hrs)` | Competing fields | Select one canonical duration source and unit. Recommended: master service stores estimated hours; labor-rate table stores money per hour. |
| `retail_pricing.Markup` | No corresponding column | Missing | Move pricing rules into a dedicated pricing-rules table. Do not infer markup from `Retail`. |
| Parts cost input | `parts_pricing.Cost` | Available but engine receives a number directly | Repository may resolve costs; engine should calculate from explicit numeric inputs. |
| Processing fees | `retail_pricing.Processing Fees` | Available but unused | Represent as a documented rate or amount in pricing rules. |
| Retail result | `retail_pricing.Retail` | Available | Treat as output/materialized data, not an engine rule. |

Confirmed failure: `PricingEngine.calculate()` indexes the absent `Hourly Rate`
column. After that is corrected, it would next fail on the absent `Markup` column.

### Related schema inconsistencies

These are not all direct engine lookups, but they affect a canonical engine contract:

- `compatibility.Service Name` stores service IDs.
- `master_services` contains `Requires Part ` with a trailing space.
- `master_services.Estimated Labor (hrs)` is mostly unpopulated while
  `labor_rates.Estimated Time` is populated in minutes.
- `labor_rates.Service Type` uses descriptive names rather than `Service ID`.
- `parts_pricing` has manufacturer/model/part/cost but no canonical SKU.
- `profit_margin` mixes supplier cost, labor cost, percentage, markup, and final
  price concepts in one table with unclear units.
- `retail_pricing` appears to be an output table but is currently used by the engine
  as though it contained pricing rules.

## Complete mismatched-column inventory

| Code location | Expected column | Actual or missing column | Impact |
|---|---|---|---|
| `CompatibilityEngine.validate` | `Service ID` | Actual column is `Service Name` | Compatibility and quote generation fail. |
| `CompatibilityRepository.find_repair` | `Service ID` | Actual column is `Service Name` | Repository compatibility lookup fails. |
| `InventoryEngine.available` | `Quantity` | Missing from `parts_catalog` | Matching inventory lookup fails. |
| `InventoryRepository.in_stock` | `Quantity` | Missing from `parts_catalog` | Repository stock lookup fails. |
| `PricingEngine.calculate` | `Hourly Rate` | Actual column is `Labor Price` | Pricing and quote generation fail. |
| `PricingEngine.calculate` | `Markup` | Missing from `retail_pricing` | Pricing fails after labor-column repair. |

## Recommended canonical schema

The names below are the target contract. Workbook display names may remain
human-readable, but code-facing adapters should expose these exact normalized fields.

### Compatibility table

Database key: `compatibility`

| Column | Type | Rule |
|---|---|---|
| `Compatibility ID` | string | Unique, nonempty. |
| `Device Family Code` | string | Foreign key to the device-family catalog. |
| `Service ID` | string | Foreign key to `master_services.Service ID`. |
| `Supported` | Boolean | Required; defaults to `False`, never truthy text. |
| `Requires Capability` | string or null | Optional technician/business capability. |
| `Notes` | string or null | Human-readable explanation. |

Unique constraint: `(Device Family Code, Service ID)`.

### Inventory table

Recommended database key: `inventory_items`.

| Column | Type | Rule |
|---|---|---|
| `SKU` | string | Unique canonical part identifier. |
| `Quantity On Hand` | integer | Required and nonnegative. |
| `Quantity Reserved` | integer | Required and nonnegative; defaults to zero. |
| `Reorder Level` | integer | Required and nonnegative; defaults to zero. |
| `Active` | Boolean | Required. |
| `Last Updated` | datetime | Required for persisted changes. |

Available quantity is `Quantity On Hand - Quantity Reserved`. Catalog description,
compatibility, supplier, and price information should remain in their own tables.

### Labor-rate table

Database key: `labor_rates`.

| Column | Type | Rule |
|---|---|---|
| `Labor Rate ID` | string | Unique. |
| `Service ID` | string | Foreign key to `master_services`. |
| `Hourly Rate` | decimal | Required, nonnegative currency value. |
| `Effective From` | date | Required. |
| `Effective To` | date or null | Null for the current open-ended rate. |
| `Active` | Boolean | Required. |

`master_services.Estimated Labor (hrs)` should be the canonical estimated duration.
If the existing minute values are retained, rename the field to
`Estimated Labor (minutes)` and convert explicitly at the boundary.

### Parts-pricing table

Database key: `parts_pricing`.

| Column | Type | Rule |
|---|---|---|
| `SKU` | string | Foreign key to the part/catalog identifier. |
| `Supplier ID` | string or null | Optional supplier relationship. |
| `Unit Cost` | decimal | Required, nonnegative currency value. |
| `Effective From` | date | Required. |
| `Effective To` | date or null | Optional. |
| `Active` | Boolean | Required. |

### Pricing-rules table

Recommended database key: `pricing_rules`.

| Column | Type | Rule |
|---|---|---|
| `Pricing Rule ID` | string | Unique. |
| `Service ID` | string or null | Null means default rule. |
| `Parts Markup Multiplier` | decimal | Example: `1.50`, not ambiguous `50`. |
| `Processing Fee Rate` | decimal | Example: `0.01` for one percent. |
| `Minimum Labor Charge` | decimal | Nonnegative currency value. |
| `Effective From` | date | Required. |
| `Effective To` | date or null | Optional. |
| `Active` | Boolean | Required. |

`retail_pricing` should become a calculated output/cache or be retired after its
consumers are migrated. It should not simultaneously be both rules and results.

## Proposed RepairManager contracts

### Minimal-disruption signatures

These signatures preserve the existing manager facade while making its semantics
match the engines:

```python
def build_quote(
    self,
    device_family_code: str,
    service_id: str,
    labor_hours: Decimal,
    parts_cost: Decimal,
) -> QuoteResult:
    ...

def calculate_price(
    self,
    labor_hours: Decimal,
    parts_cost: Decimal,
) -> PricingResult:
    ...

def check_inventory(
    self,
    sku: str,
    requested_quantity: int = 1,
) -> InventoryAvailability:
    ...

def validate_service(
    self,
    device_family_code: str,
    service_id: str,
) -> CompatibilityResult:
    ...
```

`validate_part(device, part)` should be deprecated because the current compatibility
table describes device-family/service compatibility, not device/part compatibility.
Do not silently preserve the misleading name. If part compatibility is later added,
introduce a separate contract such as:

```python
def validate_part_compatibility(
    self,
    device_id: str,
    sku: str,
) -> PartCompatibilityResult:
    ...
```

### Later request-object contract

After callers have migrated, quote generation can accept a stable request object:

```python
def build_quote(self, request: QuoteRequest) -> QuoteResult:
    ...
```

This should be a later phase, not part of the initial contract repair.

## Repository versus engine responsibilities

### Repositories retain

- Database-key and column mapping.
- DataFrame access and filtering.
- Selection of records by IDs, dates, active status, and effective range.
- Repository return standards: collections as `pandas.DataFrame`; single records as
  `pandas.Series | None`.
- Schema-presence validation at the data boundary.
- Persistence coordination through the future unit of work.

Recommended repository operations include:

```text
CompatibilityRepository.find_service(device_family_code, service_id)
InventoryRepository.get_by_sku(sku)
LaborRateRepository.current_for_service(service_id, as_of)
PartsPricingRepository.current_for_sku(sku, as_of)
PricingRuleRepository.current_for_service(service_id, as_of)
```

Repositories should not decide whether a repair is commercially acceptable or
calculate quote totals.

### Engines retain

- Business-rule evaluation over explicit inputs or repository results.
- Compatibility decision and reason construction.
- Available-quantity calculation and sufficiency decision.
- Labor, parts, fee, markup, subtotal, and retail calculations.
- Quote orchestration across compatibility and pricing results.
- Validation of numeric domains such as nonnegative hours, costs, and quantities.
- Stable typed result construction.

Engines should not know workbook names, DataFrame column strings, or openpyxl.

### Services and workflows

- Services resolve business inputs, call repositories and engines, and enforce
  application-level business rules.
- Workflows own multi-step repair/estimate/invoice state and transitions.
- `RepairManager` remains a composition/facade boundary during migration; it should
  not become another repository or workflow implementation.

## Recommended result contracts

Use stable typed results rather than conditional dictionaries:

```text
CompatibilityResult
  supported: bool
  reason: str
  requires_capability: str | None

InventoryAvailability
  sku: str
  requested_quantity: int
  available_quantity: int
  sufficient: bool

PricingResult
  labor_cost: Decimal
  parts_cost: Decimal
  processing_fees: Decimal
  subtotal: Decimal
  retail: Decimal

QuoteResult
  supported: bool
  reason: str | None
  pricing: PricingResult | None
```

Use `Decimal` with an explicit currency rounding policy.

## Phased migration

### Phase 0: Freeze and characterize

Goal: create safety without changing runtime behavior.

1. Add in-memory DataFrame contract tests for all engines.
2. Add regression tests documenting the present schema failures.
3. Record the workbook version and exact relevant columns in test fixtures.
4. Define typed result objects without changing callers.

Exit criteria:

- Tests cover supported, unsupported, missing-record, empty-table, malformed-value,
  and missing-column cases.
- Existing GUI startup remains unchanged.

### Phase 1: Add compatibility adapters

Goal: restore operations against the existing workbook before renaming columns.

1. Make repositories translate the current `Service Name` compatibility column into
   the canonical `Service ID` contract.
2. Read `Labor Price` through a temporary labor-rate adapter with documented units.
3. Do not pretend `Quantity` or `Markup` exists; return explicit unavailable/config
   errors for those operations.
4. Correct `RepairManager` parameter names and add compatibility aliases only where
   callers require a transition period.

Exit criteria:

- Compatibility works with the existing workbook.
- Pricing and inventory fail descriptively rather than with `KeyError`.
- Quote failure identifies unavailable pricing configuration.

### Phase 2: Introduce canonical workbook tables

Goal: establish durable data contracts.

1. Back up the workbook and use a disposable migration copy.
2. Rename compatibility `Service Name` to `Service ID` and validate foreign keys.
3. Add the dedicated `inventory_items` table.
4. Normalize `labor_rates` to service IDs, hourly rates, effective dates, and active
   state.
5. Normalize `parts_pricing` around SKU and unit cost.
6. Add `pricing_rules` with explicit multiplier/rate units.
7. Add new database keys to `config.database.TABLES` only when the workbook tables
   exist and validators cover them.

Exit criteria:

- All new tables load through `TableLoader`.
- Relationship validation passes.
- No engine relies on ambiguous or missing columns.

### Phase 3: Move data access into repositories

Goal: make engines independent of pandas and workbook layout.

1. Implement the repository operations listed above.
2. Inject repository interfaces or resolved domain inputs into engines.
3. Remove direct database-dictionary use from concrete engines.
4. Reduce or retire `EngineBase` after its data-access helpers have no consumers.

Exit criteria:

- Concrete engines have no DataFrame column literals.
- Repository contract tests and pure engine tests pass independently.

### Phase 4: Correct composition and eliminate duplicates

Goal: establish one engine instance per responsibility.

1. Construct compatibility, pricing, and inventory engines once.
2. Inject the shared compatibility and pricing engines into `QuoteEngine`.
3. Keep `RepairManager` as the stable facade while callers migrate to corrected
   signatures.
4. Deprecate and then remove `validate_part(device, part)` after all callers use the
   correct service-compatibility contract.

Exit criteria:

- `RepairManager` owns no duplicate engine instances.
- All callers use semantically correct method signatures.

### Phase 5: Integrate persistence and workflows

Goal: connect stable engine decisions to safe operational workflows.

1. Integrate inventory reservations with the planned unit of work.
2. Persist quote inputs, selected rules, calculated results, and rule versions for
   auditability.
3. Make repair, estimate, and invoice workflows consume typed engine results.
4. Add end-to-end tests using a disposable workbook fixture.

Exit criteria:

- A quote can be reproduced from persisted inputs and rule versions.
- Inventory reservation and rollback are transactionally safe.

## Minimal-disruption safeguards

- Preserve `RepairManager` as the caller-facing facade during phases 0-4.
- Introduce adapters before workbook column renames.
- Never migrate the production workbook in place without backup and validation.
- Add database configuration keys only after their workbook tables exist.
- Avoid GUI changes until the corrected manager contracts are covered by tests.
- Keep compatibility, pricing, and inventory migrations independently reversible.
- Use deprecation warnings and temporary aliases for renamed public methods rather
  than changing every caller in one step.
- Update `ARCHITECTURE.md`, `DEPENDENCY_GRAPH.md`, and project status after each
  completed phase.

## Recommended implementation order

1. Tests and typed results.
2. Compatibility adapter and `Supported` handling.
3. Correct `RepairManager` names and numeric contracts.
4. Canonical inventory schema.
5. Canonical labor and pricing-rule schemas.
6. Repository-based engine inputs.
7. Shared engine injection into `QuoteEngine`.
8. Workflow and persistence integration.

The first production-facing milestone should be a compatibility decision that works
against the existing workbook and a pricing/inventory path that fails with explicit
configuration errors instead of raw pandas exceptions. Full quoting should be
enabled only after the canonical pricing and inventory schemas are populated and
validated.
