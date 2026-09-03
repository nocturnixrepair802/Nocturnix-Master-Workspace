from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient

from api import app as api_app_module
from api.app import app
from models.service_pricing import ServicePricingRule
from services.pricing_rule_provider import PricingRuleProvider


class FakeMobileSentrixClient:
    def get_product(
        self,
        *,
        product_id: str | int,
    ) -> dict[str, Any]:
        assert str(product_id) == "249690"

        return {
            "entity_id": "249690",
            "sku": "107082080528",
            "name": ("OLED Assembly For iPhone 13 Pro " "(Refurbished)"),
            "customer_price": "115.40",
            "status": "1",
            "is_saleable": True,
            "is_in_stock": True,
            "in_stock_qty": 3,
        }


class FakeCatalogDatabase:
    def get_device(
        self,
        device_id: str,
    ) -> dict[str, object] | None:
        if device_id != "DEV000093":
            return None

        return {
            "device_id": "DEV000093",
            "device_type_id": "DTY000001",
            "manufacturer_id": "MFR000001",
            "manufacturer": "Apple",
            "device_family_id": "DFM000001",
            "device_family": "",
            "device_model_id": "",
            "device_model": "iPhone 13 Pro",
            "active": True,
        }


def screen_rule() -> ServicePricingRule:
    return ServicePricingRule(
        service_type_id="STY000001",
        service_type="Screen Replacement",
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


def configure_dependencies(
    monkeypatch,
    *,
    provider: PricingRuleProvider | None = None,
) -> None:
    fake_mobilesentrix = FakeMobileSentrixClient()
    fake_catalog = FakeCatalogDatabase()

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_mobilesentrix,
    )

    monkeypatch.setattr(
        api_app_module,
        "get_catalog_database",
        lambda: fake_catalog,
    )

    monkeypatch.setattr(
        api_app_module,
        "get_pricing_rule_provider",
        lambda: (
            provider
            if provider is not None
            else PricingRuleProvider(
                [
                    screen_rule(),
                ]
            )
        ),
    )


def test_service_pricing_preview(
    monkeypatch,
) -> None:
    configure_dependencies(monkeypatch)

    client = TestClient(app)

    response = client.post(
        "/api/v1/pricing/preview",
        json={
            "device_id": "DEV000093",
            "service_type_id": "STY000001",
            "supplier_product_id": "249690",
            "shipping": 10.00,
            "consumables": 5.00,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["device_id"] == "DEV000093"
    assert payload["device_model"] == "iPhone 13 Pro"
    assert payload["manufacturer_id"] == "MFR000001"
    assert payload["manufacturer"] == "Apple"

    assert payload["service_type_id"] == "STY000001"
    assert payload["service_type"] == "Screen Replacement"
    assert payload["service_category_id"] == "SC000010"

    assert payload["supplier"] == "Mobile Sentrix"
    assert payload["supplier_product_id"] == "249690"
    assert payload["supplier_sku"] == "107082080528"

    assert payload["part_name"] == ("OLED Assembly For iPhone 13 Pro " "(Refurbished)")

    assert payload["part_cost"] == 115.40
    assert payload["supplier_in_stock"] is True
    assert payload["supplier_stock_qty"] == 3

    assert payload["default_labor_hours"] == 1.00
    assert payload["labor_profile_id"] == "LAB000002"
    assert payload["labor_tier"] == "L2 Standard"

    assert payload["hourly_rate"] == 100.00
    assert payload["minimum_charge"] == 85.00

    assert payload["calculated_labor_cost"] == 100.00
    assert payload["billable_labor_cost"] == 100.00

    assert payload["shipping"] == 10.00
    assert payload["consumables"] == 5.00

    assert payload["base_direct_cost"] == 230.40

    assert payload["overhead_rate"] == 0.12
    assert payload["overhead_reserve"] == 27.65

    assert payload["warranty_rate"] == 0.05
    assert payload["warranty_reserve"] == 11.52

    assert payload["risk_rate"] == 0.04
    assert payload["risk_reserve"] == 9.22

    assert payload["processing_rate"] == 0.03
    assert payload["processing_reserve"] == 6.91

    assert payload["total_internal_cost"] == 285.70

    assert payload["target_margin"] == 0.30
    assert payload["minimum_margin"] == 0.20

    assert payload["raw_retail_price"] == 408.14
    assert payload["recommended_retail_price"] == 408.99

    assert payload["gross_profit"] == 123.29
    assert payload["pricing_status"] == "READY"

    assert payload["market_low"] is None
    assert payload["market_average"] is None
    assert payload["market_high"] is None
    assert payload["market_sample_count"] is None
    assert payload["market_position"] is None


def test_service_pricing_preview_fails_closed_without_rule(
    monkeypatch,
) -> None:
    configure_dependencies(
        monkeypatch,
        provider=PricingRuleProvider(),
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/pricing/preview",
        json={
            "device_id": "DEV000093",
            "service_type_id": "STY000001",
            "supplier_product_id": "249690",
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "No approved runtime pricing rule is available " "for STY000001."
    )


def test_service_pricing_preview_rejects_svc_identity(
    monkeypatch,
) -> None:
    configure_dependencies(monkeypatch)

    client = TestClient(app)

    response = client.post(
        "/api/v1/pricing/preview",
        json={
            "device_id": "DEV000093",
            "service_type_id": "SVC000001",
            "supplier_product_id": "249690",
        },
    )

    assert response.status_code == 422


def test_service_pricing_preview_unknown_device(
    monkeypatch,
) -> None:
    configure_dependencies(monkeypatch)

    client = TestClient(app)

    response = client.post(
        "/api/v1/pricing/preview",
        json={
            "device_id": "DEV999999",
            "service_type_id": "STY000001",
            "supplier_product_id": "249690",
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == ("Catalog device not found: DEV999999")


def test_service_pricing_preview_requires_supplier_product_id() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/pricing/preview",
        json={
            "device_id": "DEV000093",
            "service_type_id": "STY000001",
            "supplier_product_id": "",
        },
    )

    assert response.status_code == 422

    assert response.json()["detail"] == (
        "Mobile Sentrix supplier_product_id " "must not be empty."
    )
