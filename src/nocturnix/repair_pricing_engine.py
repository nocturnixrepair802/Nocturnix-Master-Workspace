"""Pure calculation engine for repair pricing."""

from decimal import ROUND_HALF_UP, Decimal

from nocturnix.repair_pricing_models import (
    RepairPricingRequest,
    RepairPricingResponse,
)

BASIS_POINTS_PER_PERCENT = 100
BASIS_POINTS_PER_WHOLE = 10_000


def _apply_basis_points(amount_cents: int, basis_points: int) -> int:
    """Apply a basis-point rate and round to the nearest cent."""

    result = (
        Decimal(amount_cents) * Decimal(basis_points) / Decimal(BASIS_POINTS_PER_WHOLE)
    )

    return int(result.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _calculate_margin_basis_points(
    gross_profit_cents: int,
    total_price_cents: int,
) -> int:
    """Calculate gross margin as basis points of total customer price."""

    if total_price_cents == 0:
        return 0

    result = (
        Decimal(gross_profit_cents)
        * Decimal(BASIS_POINTS_PER_WHOLE)
        / Decimal(total_price_cents)
    )

    return int(result.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_repair_pricing(
    request: RepairPricingRequest,
) -> RepairPricingResponse:
    """Calculate a deterministic repair pricing breakdown.

    Calculation order:

    1. Combine parts, labor, and overhead into internal cost.
    2. Apply markup to internal cost.
    3. Add the processing fee.
    4. Calculate tax on the customer subtotal.
    5. Calculate total price, gross profit, and gross margin.
    """

    internal_cost_cents = (
        request.parts_cost_cents + request.labor_cost_cents + request.overhead_cents
    )

    markup_amount_cents = _apply_basis_points(
        internal_cost_cents,
        request.markup_basis_points,
    )

    subtotal_before_tax_cents = (
        internal_cost_cents + markup_amount_cents + request.processing_fee_cents
    )

    taxable_subtotal_cents = subtotal_before_tax_cents

    tax_amount_cents = _apply_basis_points(
        taxable_subtotal_cents,
        request.tax_rate_basis_points,
    )

    total_price_cents = taxable_subtotal_cents + tax_amount_cents

    gross_profit_cents = subtotal_before_tax_cents - internal_cost_cents

    gross_margin_basis_points = _calculate_margin_basis_points(
        gross_profit_cents,
        total_price_cents,
    )

    return RepairPricingResponse(
        parts_cost_cents=request.parts_cost_cents,
        labor_cost_cents=request.labor_cost_cents,
        processing_fee_cents=request.processing_fee_cents,
        overhead_cents=request.overhead_cents,
        internal_cost_cents=internal_cost_cents,
        markup_amount_cents=markup_amount_cents,
        subtotal_before_tax_cents=subtotal_before_tax_cents,
        taxable_subtotal_cents=taxable_subtotal_cents,
        tax_amount_cents=tax_amount_cents,
        total_price_cents=total_price_cents,
        gross_profit_cents=gross_profit_cents,
        gross_margin_basis_points=gross_margin_basis_points,
    )
