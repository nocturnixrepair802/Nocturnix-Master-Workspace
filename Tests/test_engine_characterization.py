from dataclasses import fields, is_dataclass
from decimal import Decimal
from typing import get_type_hints

import pandas as pd
import pytest

from engines.compatibility_engine import CompatibilityEngine
from engines.engine_base import EngineBase
from engines.inventory_engine import InventoryEngine
from engines.pricing_engine import PricingEngine
from engines.quote_engine import QuoteEngine
from engines.results import (
    CompatibilityResult,
    InventoryAvailability,
    PricingResult,
    QuoteResult,
)
from managers.repair_manager import RepairManager


def compatibility_table(
    *,
    supported: bool = True,
    service_column: str = "Service ID",
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Device Family": "PHN",
                service_column: "SVC000001",
                "Supported": supported,
            }
        ]
    )


def pricing_database() -> dict[str, pd.DataFrame]:
    return {
        "labor_rates": pd.DataFrame([{"Hourly Rate": 100.0}]),
        "retail_pricing": pd.DataFrame([{"Markup": 1.5}]),
    }


class TestTypedResultDefinitions:
    def test_result_models_are_dataclasses(self) -> None:
        result_types = (
            CompatibilityResult,
            InventoryAvailability,
            PricingResult,
            QuoteResult,
        )

        assert all(is_dataclass(result_type) for result_type in result_types)

    def test_pricing_result_uses_decimal_fields(self) -> None:
        type_hints = get_type_hints(PricingResult)

        assert type_hints == {
            "labor_cost": Decimal,
            "parts_cost": Decimal,
            "processing_fees": Decimal,
            "subtotal": Decimal,
            "retail": Decimal,
        }

    def test_result_models_are_importable_and_constructible(self) -> None:
        pricing = PricingResult(
            labor_cost=Decimal("100.00"),
            parts_cost=Decimal("25.00"),
            processing_fees=Decimal("1.25"),
            subtotal=Decimal("125.00"),
            retail=Decimal("126.25"),
        )

        compatibility = CompatibilityResult(True, "Supported")
        inventory = InventoryAvailability("SKU-1", 1, 3, True)
        quote = QuoteResult(True, pricing=pricing)

        assert compatibility.requires_capability is None
        assert inventory.sufficient is True
        assert quote.pricing is pricing

    def test_result_models_have_only_explicit_fields(self) -> None:
        assert [field.name for field in fields(CompatibilityResult)] == [
            "supported",
            "reason",
            "requires_capability",
        ]
        assert [field.name for field in fields(InventoryAvailability)] == [
            "sku",
            "requested_quantity",
            "available_quantity",
            "sufficient",
        ]


class TestCurrentVerifiedBehavior:
    def test_missing_database_table_raises_value_error(self) -> None:
        engine = EngineBase({})

        with pytest.raises(ValueError, match="Database table 'missing' not loaded"):
            engine.get_table("missing")

    def test_supported_compatibility_row_returns_supported(self) -> None:
        engine = CompatibilityEngine(
            {"compatibility": compatibility_table(supported=True)}
        )

        assert engine.validate("PHN", "SVC000001") == {
            "supported": True,
            "reason": "Supported",
        }

    def test_unmatched_compatibility_returns_unsupported(self) -> None:
        engine = CompatibilityEngine(
            {"compatibility": compatibility_table(supported=True)}
        )

        assert engine.validate("TAB", "SVC000001") == {
            "supported": False,
            "reason": "Repair not supported.",
        }

    def test_empty_compatibility_table_returns_unsupported(self) -> None:
        table = pd.DataFrame(columns=["Device Family", "Service ID", "Supported"])
        engine = CompatibilityEngine({"compatibility": table})

        assert engine.validate("PHN", "SVC000001")["supported"] is False

    def test_inventory_unknown_sku_returns_false_without_quantity_column(self) -> None:
        inventory = pd.DataFrame([{"SKU": "OTHER"}])
        engine = InventoryEngine({"parts_catalog": inventory})

        assert engine.available("UNKNOWN", 1) is False

    def test_malformed_labor_hours_raise_type_error(self) -> None:
        engine = PricingEngine(pricing_database())

        with pytest.raises(TypeError):
            engine.calculate("not-a-number", 25.0)

    def test_repair_manager_validate_part_forwards_to_service_compatibility(self) -> None:
        database = {
            **pricing_database(),
            "compatibility": compatibility_table(supported=True),
            "parts_catalog": pd.DataFrame(columns=["SKU", "Quantity"]),
        }
        manager = RepairManager(database)

        result = manager.validate_part("PHN", "SVC000001")

        assert result["supported"] is True


class TestCurrentKnownFailures:
    def test_missing_required_compatibility_column_raises_key_error(self) -> None:
        table = pd.DataFrame([{"Device Family": "PHN"}])
        engine = CompatibilityEngine({"compatibility": table})

        with pytest.raises(KeyError, match="Service ID"):
            engine.validate("PHN", "SVC000001")

    def test_current_workbook_compatibility_column_mismatch_raises_key_error(
        self,
    ) -> None:
        table = compatibility_table(service_column="Service Name")
        engine = CompatibilityEngine({"compatibility": table})

        with pytest.raises(KeyError, match="Service ID"):
            engine.validate("PHN", "SVC000001")

    def test_matching_inventory_sku_without_quantity_raises_key_error(self) -> None:
        inventory = pd.DataFrame([{"SKU": "SKU-1"}])
        engine = InventoryEngine({"parts_catalog": inventory})

        with pytest.raises(KeyError, match="Quantity"):
            engine.available("SKU-1", 1)

    def test_pricing_without_hourly_rate_raises_key_error(self) -> None:
        database = {
            "labor_rates": pd.DataFrame([{"Labor Price": 100.0}]),
            "retail_pricing": pd.DataFrame([{"Markup": 1.5}]),
        }
        engine = PricingEngine(database)

        with pytest.raises(KeyError, match="Hourly Rate"):
            engine.calculate(1.0, 25.0)

    def test_pricing_without_markup_raises_key_error(self) -> None:
        database = {
            "labor_rates": pd.DataFrame([{"Hourly Rate": 100.0}]),
            "retail_pricing": pd.DataFrame([{"Retail": 0.0}]),
        }
        engine = PricingEngine(database)

        with pytest.raises(KeyError, match="Markup"):
            engine.calculate(1.0, 25.0)

    def test_quote_fails_through_compatibility_column_mismatch(self) -> None:
        database = {
            **pricing_database(),
            "compatibility": compatibility_table(service_column="Service Name"),
        }
        engine = QuoteEngine(database)

        with pytest.raises(KeyError, match="Service ID"):
            engine.generate("PHN", "SVC000001", 1.0, 25.0)

    def test_repair_manager_calculate_price_parameter_mismatch_raises_type_error(
        self,
    ) -> None:
        database = {
            **pricing_database(),
            "compatibility": compatibility_table(),
            "parts_catalog": pd.DataFrame(columns=["SKU", "Quantity"]),
        }
        manager = RepairManager(database)

        with pytest.raises(TypeError):
            manager.calculate_price("screen-repair", ["display"])


class TestApprovedTargetBehaviorNotImplemented:
    @pytest.mark.xfail(
        strict=True,
        reason="Target contract must honor Supported=False; current engine ignores it.",
    )
    def test_supported_false_row_is_rejected(self) -> None:
        engine = CompatibilityEngine(
            {"compatibility": compatibility_table(supported=False)}
        )

        assert engine.validate("PHN", "SVC000001")["supported"] is False

    @pytest.mark.xfail(
        strict=True,
        reason="Target pricing contract rejects negative inputs; validation is pending.",
    )
    def test_negative_pricing_inputs_are_rejected(self) -> None:
        engine = PricingEngine(pricing_database())

        with pytest.raises(ValueError, match="nonnegative"):
            engine.calculate(-1.0, -25.0)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "RepairManager target API uses validate_service; current validate_part "
            "name has the wrong semantic contract."
        ),
    )
    def test_repair_manager_exposes_validate_service_contract(self) -> None:
        database = {
            **pricing_database(),
            "compatibility": compatibility_table(),
            "parts_catalog": pd.DataFrame(columns=["SKU", "Quantity"]),
        }
        manager = RepairManager(database)

        result = manager.validate_service("PHN", "SVC000001")

        assert result["supported"] is True
