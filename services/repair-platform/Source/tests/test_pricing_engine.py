from decimal import Decimal

import pytest

from engines.pricing_engine import PricingEngine
from exceptions.pricing_exception import PricingException


def create_engine() -> PricingEngine:
    return PricingEngine()


def test_calculate_screen_replacement() -> None:
    engine = create_engine()

    result = engine.calculate(
        part_cost=Decimal("115.40"),
        default_labor_hours=Decimal("1.00"),
        hourly_rate=Decimal("100.00"),
        minimum_charge=Decimal("85.00"),
        shipping=Decimal("10.00"),
        consumables=Decimal("5.00"),
        overhead_rate=Decimal("0.12"),
        warranty_rate=Decimal("0.05"),
        risk_rate=Decimal("0.04"),
        processing_rate=Decimal("0.03"),
        target_margin=Decimal("0.30"),
        minimum_margin=Decimal("0.20"),
    )

    assert result["calculated_labor_cost"] == Decimal("100.00")
    assert result["billable_labor_cost"] == Decimal("100.00")
    assert result["base_direct_cost"] == Decimal("230.40")

    assert result["overhead_reserve"] == Decimal("27.65")
    assert result["warranty_reserve"] == Decimal("11.52")
    assert result["risk_reserve"] == Decimal("9.22")
    assert result["processing_reserve"] == Decimal("6.91")

    assert result["total_internal_cost"] == Decimal("285.70")
    assert result["raw_retail_price"] == Decimal("408.14")
    assert result["recommended_retail_price"] == Decimal("408.99")

    assert result["gross_profit"] == Decimal("123.29")
    assert result["pricing_status"] == "READY"


def test_minimum_labor_charge_is_enforced() -> None:
    engine = create_engine()

    result = engine.calculate(
        part_cost=Decimal("10.00"),
        default_labor_hours=Decimal("0.25"),
        hourly_rate=Decimal("85.00"),
        minimum_charge=Decimal("65.00"),
        target_margin=Decimal("0.30"),
        minimum_margin=Decimal("0.20"),
    )

    assert result["calculated_labor_cost"] == Decimal("21.25")
    assert result["billable_labor_cost"] == Decimal("65.00")


@pytest.mark.parametrize(
    ("raw_price", "expected"),
    [
        ("143.12", "143.99"),
        ("143.99", "143.99"),
        ("144.00", "144.99"),
        ("144.01", "144.99"),
        ("144.99", "144.99"),
        ("145.00", "145.99"),
    ],
)
def test_round_to_99(
    raw_price: str,
    expected: str,
) -> None:
    assert PricingEngine._round_to_99(Decimal(raw_price)) == Decimal(expected)


def test_target_margin_must_be_less_than_one() -> None:
    engine = create_engine()

    with pytest.raises(
        PricingException,
        match="target_margin must be less than 1.00",
    ):
        engine.calculate(
            part_cost=10,
            default_labor_hours=1,
            hourly_rate=100,
            minimum_charge=85,
            target_margin=1,
            minimum_margin=0.20,
        )


def test_minimum_margin_cannot_exceed_target() -> None:
    engine = create_engine()

    with pytest.raises(
        PricingException,
        match="minimum_margin cannot exceed target_margin",
    ):
        engine.calculate(
            part_cost=10,
            default_labor_hours=1,
            hourly_rate=100,
            minimum_charge=85,
            target_margin=0.20,
            minimum_margin=0.30,
        )


def test_negative_pricing_values_are_rejected() -> None:
    engine = create_engine()

    with pytest.raises(
        PricingException,
        match="cannot be negative",
    ):
        engine.calculate(
            part_cost=-1,
            default_labor_hours=1,
            hourly_rate=100,
            minimum_charge=85,
            target_margin=0.30,
            minimum_margin=0.20,
        )


def test_percentage_must_be_decimal_fraction() -> None:
    engine = create_engine()

    with pytest.raises(
        PricingException,
        match="overhead_rate must be expressed",
    ):
        engine.calculate(
            part_cost=10,
            default_labor_hours=1,
            hourly_rate=100,
            minimum_charge=85,
            overhead_rate=12,
            target_margin=0.30,
            minimum_margin=0.20,
        )
