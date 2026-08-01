"""Tests for the pure repair pricing engine."""

from typing import Any

import pytest
from pydantic import ValidationError

from nocturnix.repair_pricing_engine import calculate_repair_pricing
from nocturnix.repair_pricing_models import RepairPricingRequest


def test_calculate_repair_pricing_with_zero_tax() -> None:
    request = RepairPricingRequest(
        parts_cost_cents=10_000,
        labor_cost_cents=5_000,
        processing_fee_cents=300,
        overhead_cents=1_000,
        markup_basis_points=2_500,
        tax_rate_basis_points=0,
    )

    result = calculate_repair_pricing(request)

    assert result.internal_cost_cents == 16_000
    assert result.markup_amount_cents == 4_000
    assert result.subtotal_before_tax_cents == 20_300
    assert result.tax_amount_cents == 0
    assert result.total_price_cents == 20_300
    assert result.gross_profit_cents == 4_300
    assert result.gross_margin_basis_points == 2_118


def test_calculate_repair_pricing_with_sales_tax() -> None:
    request = RepairPricingRequest(
        parts_cost_cents=8_000,
        labor_cost_cents=4_000,
        processing_fee_cents=0,
        overhead_cents=0,
        markup_basis_points=2_000,
        tax_rate_basis_points=725,
    )

    result = calculate_repair_pricing(request)

    assert result.internal_cost_cents == 12_000
    assert result.markup_amount_cents == 2_400
    assert result.subtotal_before_tax_cents == 14_400
    assert result.tax_amount_cents == 1_044
    assert result.total_price_cents == 15_444
    assert result.gross_profit_cents == 2_400


def test_calculate_parts_only_repair() -> None:
    request = RepairPricingRequest(
        parts_cost_cents=7_500,
        markup_basis_points=1_000,
    )

    result = calculate_repair_pricing(request)

    assert result.internal_cost_cents == 7_500
    assert result.markup_amount_cents == 750
    assert result.total_price_cents == 8_250


def test_calculate_labor_only_repair() -> None:
    request = RepairPricingRequest(
        labor_cost_cents=10_000,
        markup_basis_points=1_500,
    )

    result = calculate_repair_pricing(request)

    assert result.internal_cost_cents == 10_000
    assert result.markup_amount_cents == 1_500
    assert result.total_price_cents == 11_500


def test_processing_fee_and_overhead_are_included() -> None:
    request = RepairPricingRequest(
        parts_cost_cents=5_000,
        labor_cost_cents=2_000,
        processing_fee_cents=250,
        overhead_cents=500,
        markup_basis_points=0,
    )

    result = calculate_repair_pricing(request)

    assert result.internal_cost_cents == 7_500
    assert result.subtotal_before_tax_cents == 7_750
    assert result.gross_profit_cents == 250
    assert result.total_price_cents == 7_750


def test_basis_point_calculation_rounds_half_up() -> None:
    request = RepairPricingRequest(
        parts_cost_cents=101,
        markup_basis_points=500,
    )

    result = calculate_repair_pricing(request)

    assert result.markup_amount_cents == 5
    assert result.total_price_cents == 106


def test_zero_price_returns_zero_margin() -> None:
    result = calculate_repair_pricing(RepairPricingRequest())

    assert result.internal_cost_cents == 0
    assert result.total_price_cents == 0
    assert result.gross_profit_cents == 0
    assert result.gross_margin_basis_points == 0


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("parts_cost_cents", -1),
        ("labor_cost_cents", -1),
        ("processing_fee_cents", -1),
        ("overhead_cents", -1),
        ("markup_basis_points", -1),
        ("tax_rate_basis_points", -1),
        ("tax_rate_basis_points", 10_001),
    ],
)
def test_pricing_request_rejects_invalid_values(
    field_name: str,
    value: int,
) -> None:
    with pytest.raises(ValidationError):
        RepairPricingRequest(**{field_name: value})


def test_pricing_request_rejects_unknown_fields() -> None:
    request_data: dict[str, Any] = {
        "parts_cost_cents": 1000,
        "labor_cost_cents": 2000,
        "processing_fee_cents": 0,
        "overhead_cents": 0,
        "markup_basis_points": 0,
        "tax_rate_basis_points": 0,
        "unexpected_value": "invalid",
    }

    with pytest.raises(ValidationError):
        RepairPricingRequest.model_validate(request_data)
