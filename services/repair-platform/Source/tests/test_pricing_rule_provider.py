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


def test_base_and_variant_can_share_canonical_service_type() -> None:
    base = pricing_rule(
        service_type_id="STY000055",
        service_type="Diagnostic",
    )

    variant = ServicePricingRule(
        service_type_id="STY000055",
        service_type="Diagnostic",
        service_category_id="SC000009",
        default_labor_hours=Decimal("1.50"),
        labor_profile_id="LAB000003",
        labor_tier="L3 Advanced",
        hourly_rate=Decimal("125.00"),
        minimum_charge=Decimal("110.00"),
        target_margin=Decimal("0.85"),
        minimum_margin=Decimal("0.65"),
        overhead_rate=Decimal("0.12"),
        warranty_rate=Decimal("0.01"),
        risk_rate=Decimal("0.02"),
        processing_rate=Decimal("0.03"),
        variant_key="ADVANCED_DIAGNOSTIC",
        variant_name="Advanced Diagnostic",
    )

    provider = PricingRuleProvider(
        [
            base,
            variant,
        ]
    )

    assert provider.count() == 2

    assert provider.get("STY000055") is base

    assert (
        provider.get(
            "STY000055",
            "ADVANCED_DIAGNOSTIC",
        )
        is variant
    )


def test_variant_key_is_case_insensitive() -> None:
    variant = ServicePricingRule(
        service_type_id="STY000055",
        service_type="Diagnostic",
        service_category_id="SC000009",
        default_labor_hours=Decimal("1.50"),
        labor_profile_id="LAB000003",
        labor_tier="L3 Advanced",
        hourly_rate=Decimal("125.00"),
        minimum_charge=Decimal("110.00"),
        target_margin=Decimal("0.85"),
        minimum_margin=Decimal("0.65"),
        overhead_rate=Decimal("0.12"),
        warranty_rate=Decimal("0.01"),
        risk_rate=Decimal("0.02"),
        processing_rate=Decimal("0.03"),
        variant_key="ADVANCED_DIAGNOSTIC",
        variant_name="Advanced Diagnostic",
    )

    provider = PricingRuleProvider([variant])

    assert provider.contains(
        "STY000055",
        "advanced_diagnostic",
    )


def test_duplicate_same_service_type_and_variant_is_rejected() -> None:
    first = pricing_rule(
        service_type_id="STY000055",
        service_type="Diagnostic",
    )

    second = pricing_rule(
        service_type_id="STY000055",
        service_type="Diagnostic",
    )

    with pytest.raises(
        DuplicatePricingRuleError,
        match="STY000055",
    ):
        PricingRuleProvider(
            [
                first,
                second,
            ]
        )


def test_same_service_type_with_different_variants_is_not_duplicate() -> None:
    first = ServicePricingRule(
        service_type_id="STY000055",
        service_type="Diagnostic",
        service_category_id="SC000009",
        default_labor_hours=Decimal("0.75"),
        labor_profile_id="LAB000002",
        labor_tier="L2 Standard",
        hourly_rate=Decimal("100.00"),
        minimum_charge=Decimal("85.00"),
        target_margin=Decimal("0.85"),
        minimum_margin=Decimal("0.65"),
        overhead_rate=Decimal("0.12"),
        warranty_rate=Decimal("0.01"),
        risk_rate=Decimal("0.02"),
        processing_rate=Decimal("0.03"),
        variant_key="BASIC_DIAGNOSTIC",
        variant_name="Basic Diagnostic",
    )

    second = ServicePricingRule(
        service_type_id="STY000055",
        service_type="Diagnostic",
        service_category_id="SC000009",
        default_labor_hours=Decimal("1.50"),
        labor_profile_id="LAB000003",
        labor_tier="L3 Advanced",
        hourly_rate=Decimal("125.00"),
        minimum_charge=Decimal("110.00"),
        target_margin=Decimal("0.85"),
        minimum_margin=Decimal("0.65"),
        overhead_rate=Decimal("0.12"),
        warranty_rate=Decimal("0.01"),
        risk_rate=Decimal("0.02"),
        processing_rate=Decimal("0.03"),
        variant_key="ADVANCED_DIAGNOSTIC",
        variant_name="Advanced Diagnostic",
    )

    provider = PricingRuleProvider(
        [
            first,
            second,
        ]
    )

    assert provider.count() == 2
