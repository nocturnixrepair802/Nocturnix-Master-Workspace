# Business Rules

Last updated: 2026-07-22
Status: Documentation baseline; target rules are not implemented

## Evidence classification

- **Verified current behavior** is confirmed by source inspection and read-only calls
  against the current workbook.
- **Broken or undefined behavior** identifies failed contracts or rules for which the
  repository/workbook provides insufficient evidence.
- **Approved target behavior** records the direction established by the Engine
  Refactor Plan and ADRs. It must not be read as current functionality.

## Compatibility

### Verified current behavior

- `CompatibilityEngine.validate(device_family, service_id)` loads the `compatibility`
  DataFrame directly.
- It attempts to match device family plus service ID.
- If no match exists, it returns `supported=False` with a generic reason.
- If a match exists, the source currently returns `supported=True` without reading
  the row's `Supported` value.
- The workbook includes `Supported`, `Requires Capability`, and `Notes` fields.

### Broken or undefined behavior

- The engine expects `Service ID`; the workbook column is `Service Name` even though
  its values are service IDs. Current validation raises `KeyError: 'Service ID'`.
- Explicit `Supported=False` rows are ignored by the algorithm.
- Capability requirements and notes are ignored.
- Duplicate family/service rows have no precedence rule.
- Family codes versus family names are not validated.
- Behavior for null or malformed Boolean values is undefined.

### Approved target behavior

1. A compatibility repository resolves exactly one record by canonical `Device Family
   Code` and `Service ID`.
2. No record means unsupported unless a future explicit default policy is approved.
3. `Supported` controls the decision; presence of a row alone is insufficient.
4. The result includes a reason and optional required capability.
5. The compatibility engine evaluates business meaning and does not know workbook
   column aliases.
6. `(Device Family Code, Service ID)` is the proposed unique pair after duplicate
   validation.

### Unresolved questions

- Does a missing row always mean unsupported, or unknown/manual review?
- How is `Requires Capability` matched against technician or business capabilities?
- Can model-specific compatibility override family compatibility?
- What user-facing reason should be shown when notes are empty?

## Pricing

### Verified current behavior

- `PricingEngine.calculate(labor_hours, parts_cost)` attempts to load the first row of
  `labor_rates` and `retail_pricing`.
- It intends to calculate labor cost as hours multiplied by an hourly rate, add parts
  cost, then multiply the subtotal by a markup.
- It returns labor cost, parts cost, subtotal, and rounded retail as a dictionary.

### Broken or undefined behavior

- `labor_rates` has `Labor Price`, not the expected `Hourly Rate`; current calls fail.
- `retail_pricing` has no `Markup`; pricing would fail there next.
- The first-row selection ignores service, effective date, active state, and rate type.
- It is unknown whether `Labor Price` is hourly or fixed.
- It is unknown whether `Estimated Time` is minutes.
- Markup multiplier versus percentage semantics are undefined.
- Processing-fee rules are undefined and inconsistent across tables.
- Taxes, minimum charges, discounts, warranties, and rounding policy are undefined.
- Float arithmetic is used for money.
- Negative or nonnumeric values are not rejected.

### Approved target behavior

1. Money uses `Decimal` and an explicit currency rounding policy.
2. Numeric inputs must be finite and nonnegative.
3. Repositories select the applicable labor rate, part cost, and pricing rule by stable
   identifiers, effective date, and active state.
4. The pricing engine receives explicit values and calculates labor, parts markup,
   processing fees, subtotal, and retail without DataFrame access.
5. Markup multipliers and fee rates use unambiguous decimal units.
6. Pricing returns a stable typed result with all monetary components.
7. Persisted quotes record rule/input versions sufficiently to reproduce a result.

### Unresolved questions

- Is labor billed hourly, as a fixed service charge, or by a hybrid rule?
- Which table is authoritative for estimated labor duration?
- What is the approved parts markup formula?
- Are processing fees percentages, fixed amounts, or both?
- When are taxes applied, and which services/parts are taxable?
- What minimum charges, discounts, warranty adjustments, or rounding rules apply?

## Inventory

### Verified current behavior

- `InventoryEngine.available(sku, requested_quantity=1)` reads `parts_catalog`.
- An unknown SKU returns `False` before quantity access.
- A matching SKU would attempt to compare `Quantity` with the requested amount.

### Broken or undefined behavior

- `parts_catalog` has `SKU` but no `Quantity`; a matching row risks
  `KeyError: 'Quantity'`.
- The current table is a catalog/pricing/export structure, not an inventory ledger.
- The only current catalog row is blank.
- Reservations, committed quantities, adjustments, locations, reorder levels,
  negative stock, and concurrent updates are undefined.
- Zero or negative requested quantities are not rejected.

### Approved target behavior

1. Inventory data lives in planned `inventory_items`, not `parts_catalog`.
2. A repository retrieves an inventory record by canonical SKU.
3. Available quantity is proposed as `Quantity On Hand - Quantity Reserved`.
4. Requested quantity must be a positive integer.
5. The engine returns a typed result containing SKU, requested quantity, available
   quantity, and sufficiency.
6. Reservation, commit, and rollback will be coordinated by the planned unit of work,
   not performed as an unprotected engine mutation.
7. Until inventory schema exists, inventory operations fail explicitly as unavailable
   rather than fabricating stock.

### Unresolved questions

- Is inventory tracked globally or by location/bin?
- When is stock reserved and when is it decremented?
- Are negative stock and backorders permitted?
- How are returns, damaged stock, and manual adjustments represented?
- Is SKU globally unique across suppliers?

## Quote generation

### Verified current behavior

- `QuoteEngine.generate()` validates compatibility first.
- Unsupported compatibility returns immediately without pricing.
- Supported compatibility calls `PricingEngine.calculate()`.
- `RepairManager.build_quote()` forwards device family, service ID, labor hours, and
  parts cost.
- `QuoteEngine` constructs its own pricing and compatibility engine instances in
  addition to those owned by `RepairManager`.

### Broken or undefined behavior

- Quote generation currently fails at compatibility because of the service-column
  mismatch.
- If compatibility were repaired, pricing would fail on its schema mismatches.
- Supported and unsupported dictionaries have different shapes.
- Quote identifiers, expiration, taxes, customer/device context, selected parts,
  audit data, and persistence are undefined.
- `RepairManager.calculate_price(service, parts)` does not match the pricing engine's
  numeric contract.
- `RepairManager.validate_part(device, part)` actually forwards values to a
  device-family/service compatibility operation.

### Approved target behavior

1. `RepairManager` remains the stable facade during migration.
2. Compatibility is evaluated before pricing.
3. A quote is priced only when the service is supported and required capabilities are
   satisfied or explicitly reviewed.
4. Quote inputs use canonical device-family code, service ID, labor hours, and parts
   cost during the minimal-disruption phase.
5. The result uses a stable typed `QuoteResult`, with optional pricing and a reason.
6. Pricing and compatibility engines are constructed once and injected into
   `QuoteEngine`.
7. Later persistence records inputs, outputs, and rule versions for reproducibility.

### Unresolved questions

- Who may override unsupported compatibility or missing capability?
- How long is a quote valid?
- Are taxes and discounts part of quote generation or invoicing?
- Must inventory be available to issue a quote, or only to schedule/start repair?
- What customer/device/ticket identifiers are required on a persisted quote?
- When does an estimate become an accepted repair authorization?

## Governance

Unresolved questions must be decided through an ADR, approved requirements, or an
explicit owner decision before implementation. Tests should encode approved rules;
they must not silently turn sample workbook values into policy.
