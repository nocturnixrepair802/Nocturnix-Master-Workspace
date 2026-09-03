from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from services.pricing_rule_loader import (
    PricingRuleApprovalError,
    PricingRuleFileNotFoundError,
    PricingRuleFormatError,
    PricingRuleLoader,
)


def valid_rule() -> dict[str, object]:
    return {
        "service_type_id": "STY000001",
        "service_type": "Screen Replacement",
        "service_category_id": "SC000010",
        "default_labor_hours": "1.00",
        "labor_profile_id": "LAB000002",
        "labor_tier": "L2 Standard",
        "hourly_rate": "100.00",
        "minimum_charge": "85.00",
        "target_margin": "0.30",
        "minimum_margin": "0.20",
        "overhead_rate": "0.12",
        "warranty_rate": "0.05",
        "risk_rate": "0.04",
        "processing_rate": "0.03",
        "rounding_rule": "End in .99",
    }


def write_artifact(
    path: Path,
    *,
    status: str = "APPROVED",
    schema_version: str = "1.0",
    rules: list[dict[str, object]] | None = None,
) -> None:
    payload = {
        "schema_version": schema_version,
        "rule_set_id": "PRSET000001",
        "status": status,
        "rules": (rules if rules is not None else [valid_rule()]),
    }

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_load_approved_artifact(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    write_artifact(path)

    rules = PricingRuleLoader(path).load()

    assert len(rules) == 1

    rule = rules[0]

    assert rule.service_type_id == "STY000001"
    assert rule.service_type == "Screen Replacement"
    assert rule.service_category_id == "SC000010"

    assert rule.default_labor_hours == Decimal("1.00")
    assert rule.hourly_rate == Decimal("100.00")
    assert rule.minimum_charge == Decimal("85.00")

    assert rule.target_margin == Decimal("0.30")
    assert rule.minimum_margin == Decimal("0.20")

    assert rule.overhead_rate == Decimal("0.12")
    assert rule.warranty_rate == Decimal("0.05")
    assert rule.risk_rate == Decimal("0.04")
    assert rule.processing_rate == Decimal("0.03")

    assert rule.variant_key == "BASE"
    assert rule.variant_name is None


def test_missing_artifact_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(
        PricingRuleFileNotFoundError,
        match="missing.json",
    ):
        PricingRuleLoader(path).load()


def test_invalid_json_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    path.write_text(
        "{bad json",
        encoding="utf-8",
    )

    with pytest.raises(
        PricingRuleFormatError,
        match="valid JSON",
    ):
        PricingRuleLoader(path).load()


def test_unapproved_artifact_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    write_artifact(
        path,
        status="PENDING REVIEW",
    )

    with pytest.raises(
        PricingRuleApprovalError,
        match="APPROVED",
    ):
        PricingRuleLoader(path).load()


def test_unsupported_schema_version_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    write_artifact(
        path,
        schema_version="2.0",
    )

    with pytest.raises(
        PricingRuleFormatError,
        match="schema_version",
    ):
        PricingRuleLoader(path).load()


def test_duplicate_base_service_type_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    write_artifact(
        path,
        rules=[
            valid_rule(),
            valid_rule(),
        ],
    )

    with pytest.raises(
        PricingRuleFormatError,
        match="Duplicate pricing rule",
    ):
        PricingRuleLoader(path).load()


@pytest.mark.parametrize(
    "service_type_id",
    [
        "",
        "SVC000001",
        "STY1",
        "STYABC001",
    ],
)
def test_invalid_service_type_identity_is_rejected(
    tmp_path: Path,
    service_type_id: str,
) -> None:
    path = tmp_path / "pricing_rules.json"

    rule = valid_rule()
    rule["service_type_id"] = service_type_id

    write_artifact(
        path,
        rules=[rule],
    )

    with pytest.raises(
        PricingRuleFormatError,
        match="service_type_id",
    ):
        PricingRuleLoader(path).load()


def test_invalid_category_identity_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    rule = valid_rule()
    rule["service_category_id"] = "CATEGORY"

    write_artifact(
        path,
        rules=[rule],
    )

    with pytest.raises(
        PricingRuleFormatError,
        match="service_category_id",
    ):
        PricingRuleLoader(path).load()


def test_invalid_labor_identity_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    rule = valid_rule()
    rule["labor_profile_id"] = "NSLC-001"

    write_artifact(
        path,
        rules=[rule],
    )

    with pytest.raises(
        PricingRuleFormatError,
        match="labor_profile_id",
    ):
        PricingRuleLoader(path).load()


def test_non_numeric_rate_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    rule = valid_rule()
    rule["hourly_rate"] = "not-a-number"

    write_artifact(
        path,
        rules=[rule],
    )

    with pytest.raises(
        PricingRuleFormatError,
        match="hourly_rate",
    ):
        PricingRuleLoader(path).load()


def test_empty_rule_set_is_allowed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    write_artifact(
        path,
        rules=[],
    )

    rules = PricingRuleLoader(path).load()

    assert rules == ()


def test_load_pricing_variant(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    rule = valid_rule()
    rule["service_type_id"] = "STY000055"
    rule["service_type"] = "Diagnostic"
    rule["service_category_id"] = "SC000009"
    rule["variant_key"] = "ADVANCED_DIAGNOSTIC"
    rule["variant_name"] = "Advanced Diagnostic"

    write_artifact(
        path,
        rules=[rule],
    )

    rules = PricingRuleLoader(path).load()

    assert len(rules) == 1

    loaded = rules[0]

    assert loaded.service_type_id == "STY000055"
    assert loaded.variant_key == "ADVANCED_DIAGNOSTIC"
    assert loaded.variant_name == "Advanced Diagnostic"


def test_base_and_variant_for_same_service_type_can_load(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    base = valid_rule()
    base["service_type_id"] = "STY000055"
    base["service_type"] = "Diagnostic"
    base["service_category_id"] = "SC000009"

    variant = valid_rule()
    variant["service_type_id"] = "STY000055"
    variant["service_type"] = "Diagnostic"
    variant["service_category_id"] = "SC000009"
    variant["variant_key"] = "ADVANCED_DIAGNOSTIC"
    variant["variant_name"] = "Advanced Diagnostic"
    variant["default_labor_hours"] = "1.50"
    variant["labor_profile_id"] = "LAB000003"
    variant["labor_tier"] = "L3 Advanced"
    variant["hourly_rate"] = "125.00"
    variant["minimum_charge"] = "110.00"

    write_artifact(
        path,
        rules=[
            base,
            variant,
        ],
    )

    rules = PricingRuleLoader(path).load()

    assert len(rules) == 2

    assert rules[0].service_type_id == "STY000055"
    assert rules[0].variant_key == "BASE"

    assert rules[1].service_type_id == "STY000055"
    assert rules[1].variant_key == "ADVANCED_DIAGNOSTIC"
    assert rules[1].variant_name == "Advanced Diagnostic"


def test_duplicate_same_service_type_and_variant_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    first = valid_rule()
    first["service_type_id"] = "STY000055"
    first["variant_key"] = "ADVANCED_DIAGNOSTIC"

    second = valid_rule()
    second["service_type_id"] = "STY000055"
    second["variant_key"] = "advanced_diagnostic"

    write_artifact(
        path,
        rules=[
            first,
            second,
        ],
    )

    with pytest.raises(
        PricingRuleFormatError,
        match="STY000055.*ADVANCED_DIAGNOSTIC",
    ):
        PricingRuleLoader(path).load()


def test_approved_artifact_allows_additional_governance_metadata(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pricing_rules.json"

    payload = {
        "schema_version": "1.0",
        "rule_set_id": "PRSET000001",
        "status": "APPROVED",
        "approval": {
            "candidate_sha256": "abc123",
            "approved_by": "test-approver",
            "approved_at": "2026-09-03T18:00:00Z",
        },
        "rules": [
            valid_rule(),
        ],
    }

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    rules = PricingRuleLoader(path).load()

    assert len(rules) == 1
    assert rules[0].service_type_id == "STY000001"
