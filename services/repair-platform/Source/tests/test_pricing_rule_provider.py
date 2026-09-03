from decimal import Decimal

import pytest

from models.service_pricing import ServicePricingRule
from services.pricing_rule_provider import (
    DuplicatePricingRuleError,
    PricingRuleNotFoundError,
    PricingRuleProvider,
)


def pricing_rule(
    service_type_id: str = "STY000001",
    service_type: str = "Screen Replacement",
) -> ServicePricingRule:
    return ServicePricingRule(
        service_type_id=service_type_id,
        service_type=service_type,
        service_category_id="SC000010",
        default_labor_hours=Decimal("1.00"),
        labor_profile_id="LAB000002",
        labor_tier="L2 Standard",
        hourly_rate=Decimal("100.00"),
        minimum_charge=Decimal("85.00"),
        target_margin=Decimal("0.30"),
        minimum_margin=Decimal("0.20"),
        overhead_rate=Decimal("0.12"),
        warranty_rate=Decimal("0.05"),
        risk_rate=Decimal("0.04"),
        processing_rate=Decimal("0.03"),
    )


def test_empty_provider() -> None:
    provider = PricingRuleProvider()

    assert provider.count() == 0
    assert provider.all() == ()


def test_get_rule() -> None:
    rule = pricing_rule()

    provider = PricingRuleProvider([rule])

    assert provider.get("STY000001") is rule


def test_get_optional_returns_none_for_unknown_rule() -> None:
    provider = PricingRuleProvider()

    assert provider.get_optional("STY999999") is None


def test_missing_rule_raises_not_found() -> None:
    provider = PricingRuleProvider()

    with pytest.raises(
        PricingRuleNotFoundError,
        match="STY999999",
    ):
        provider.get("STY999999")


def test_contains_rule() -> None:
    provider = PricingRuleProvider([pricing_rule()])

    assert provider.contains("STY000001") is True
    assert provider.contains("STY999999") is False


def test_all_returns_supplied_rules() -> None:
    screen = pricing_rule()

    battery = pricing_rule(
        service_type_id="STY000007",
        service_type="Battery Replacement",
    )

    provider = PricingRuleProvider(
        [
            screen,
            battery,
        ]
    )

    assert provider.all() == (
        screen,
        battery,
    )

    assert provider.count() == 2


def test_duplicate_service_type_rule_is_rejected() -> None:
    first = pricing_rule()

    second = pricing_rule(
        service_type_id="STY000001",
        service_type="Different Name",
    )

    with pytest.raises(
        DuplicatePricingRuleError,
        match="STY000001",
    ):
        PricingRuleProvider(
            [
                first,
                second,
            ]
        )
