# ADR-005: Decimal for Monetary Calculations

- Status: Accepted
- Date: 2026-07-22

## Context

Current pricing code converts workbook values to `float` and rounds only the final
retail result. Binary floating-point arithmetic can introduce monetary errors, and no
explicit currency rounding policy currently exists.

## Decision

- New and refactored monetary calculation contracts use `decimal.Decimal`.
- Inputs are converted at application boundaries from strings, integers, or workbook
  numeric values using documented conversion rules.
- Monetary values are finite and nonnegative unless an explicitly approved adjustment
  rule permits otherwise.
- Currency quantization and rounding mode must be explicit and covered by tests.
- Persisted quotes retain sufficient input and rule precision for reproduction.

## Consequences

- Pricing results become deterministic and appropriate for currency.
- pandas/openpyxl boundary adapters must convert values carefully; direct
  `Decimal(float_value)` conversion is not acceptable.
- GUI formatting remains separate from calculation precision.
- Existing float-based code requires staged migration.

## Alternatives considered

- Continue using float with final rounding: rejected because intermediate error and
  inconsistent rounding remain possible.
- Store money only as integer cents: viable, but rejected for the current migration
  because workbook values and percentage rules still need decimal conversion.
- Use a third-party money library: deferred until currency/multi-currency requirements
  exist.
