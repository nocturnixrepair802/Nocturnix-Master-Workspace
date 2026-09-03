from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api import app as api_app_module
from api.app import app
from models.service_pricing import ServicePricingRule
from persistence.operations_db import OperationsDatabase
from services.pricing_rule_provider import PricingRuleProvider
from services.service_pricing_catalog_service import (
    ServicePricingCatalogService,
)


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
            "name": ("OLED Assembly For iPhone 13 Pro (Refurbished)"),
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
        variant_key="BASE",
        variant_name=None,
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
        rounding_rule="End in .99",
    )


@pytest.fixture
def pricing_catalog_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, OperationsDatabase]:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    fake_mobilesentrix = FakeMobileSentrixClient()
    fake_catalog = FakeCatalogDatabase()

    provider = PricingRuleProvider(
        [
            screen_rule(),
        ]
    )

    monkeypatch.setattr(
        api_app_module,
        "get_database",
        lambda: database,
    )

    monkeypatch.setattr(
        api_app_module,
        "get_catalog_database",
        lambda: fake_catalog,
    )

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_mobilesentrix,
    )

    monkeypatch.setattr(
        api_app_module,
        "get_pricing_rule_provider",
        lambda: provider,
    )

    app.dependency_overrides[api_app_module.get_service_pricing_catalog_service] = (
        lambda: ServicePricingCatalogService(
            operations_database=database,
        )
    )

    client = TestClient(app)

    try:
        yield client, database

    finally:
        app.dependency_overrides.clear()


def save_pricing_record(
    client: TestClient,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/pricing/catalog",
        json={
            "device_id": "DEV000093",
            "service_type_id": "STY000001",
            "variant_key": "BASE",
            "supplier_product_id": "249690",
            "shipping": 10.00,
            "consumables": 5.00,
        },
    )

    assert response.status_code == 200

    return response.json()


def test_save_service_pricing_catalog(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, database = pricing_catalog_client

    payload = save_pricing_record(client)

    assert payload["pricing_record_id"] == "PRC000001"
    assert payload["catalog_device_id"] == "DEV000093"

    assert payload["service_type_id"] == "STY000001"
    assert payload["service_type"] == "Screen Replacement"
    assert payload["service_category_id"] == "SC000010"

    assert payload["variant_key"] == "BASE"
    assert payload["variant_name"] is None

    assert payload["supplier"] == "Mobile Sentrix"
    assert payload["supplier_product_id"] == "249690"
    assert payload["supplier_sku"] == "107082080528"

    assert payload["part_cost"] == 115.40
    assert payload["supplier_in_stock"] is True
    assert payload["supplier_stock_qty"] == 3

    assert payload["billable_labor_cost"] == 100.00
    assert payload["shipping"] == 10.00
    assert payload["consumables"] == 5.00

    assert payload["base_direct_cost"] == 230.40
    assert payload["total_internal_cost"] == 285.70
    assert payload["recommended_price"] == 408.99
    assert payload["gross_profit"] == 123.29

    assert payload["pricing_status"] == "READY"

    assert payload["approved_price"] is None
    assert payload["approval_status"] == "DRAFT"
    assert payload["approved_at"] is None
    assert payload["approved_by"] is None

    stored = database.get_service_pricing_record("PRC000001")

    assert stored is not None
    assert stored["part_cost_cents"] == 11540
    assert stored["recommended_price_cents"] == 40899


def test_save_refreshes_existing_catalog_identity(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, database = pricing_catalog_client

    first = save_pricing_record(client)
    second = save_pricing_record(client)

    assert first["pricing_record_id"] == "PRC000001"
    assert second["pricing_record_id"] == "PRC000001"

    records = database.list_service_pricing_records()

    assert len(records) == 1


def test_get_service_pricing_catalog_record(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = pricing_catalog_client

    save_pricing_record(client)

    response = client.get("/api/v1/pricing/catalog/PRC000001")

    assert response.status_code == 200

    payload = response.json()

    assert payload["pricing_record_id"] == "PRC000001"
    assert payload["catalog_device_id"] == "DEV000093"
    assert payload["service_type_id"] == "STY000001"


def test_get_unknown_service_pricing_catalog_record(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = pricing_catalog_client

    response = client.get("/api/v1/pricing/catalog/PRC999999")

    assert response.status_code == 404
    assert response.json()["detail"] == ("Service pricing record not found.")


def test_list_service_pricing_catalog(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = pricing_catalog_client

    save_pricing_record(client)

    response = client.get(
        "/api/v1/pricing/catalog",
        params={
            "catalog_device_id": "DEV000093",
            "service_type_id": "STY000001",
            "variant_key": "BASE",
            "approval_status": "DRAFT",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["pricing_record_id"] == "PRC000001"


def test_approve_service_pricing_catalog_record(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, database = pricing_catalog_client

    save_pricing_record(client)

    response = client.post(
        "/api/v1/pricing/catalog/PRC000001/approve",
        json={
            "approved_price": 399.99,
            "approved_by": "Ryan Brown",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["pricing_record_id"] == "PRC000001"
    assert payload["approval_status"] == "APPROVED"
    assert payload["approved_price"] == 399.99
    assert payload["approved_by"] == "Ryan Brown"
    assert payload["approved_at"] is not None

    stored = database.get_service_pricing_record("PRC000001")

    assert stored is not None
    assert stored["approval_status"] == "APPROVED"
    assert stored["approved_price_cents"] == 39999


def test_approve_unknown_service_pricing_record(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = pricing_catalog_client

    response = client.post(
        "/api/v1/pricing/catalog/PRC999999/approve",
        json={
            "approved_price": 399.99,
            "approved_by": "Ryan Brown",
        },
    )

    assert response.status_code == 404


def test_second_approval_returns_conflict(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = pricing_catalog_client

    save_pricing_record(client)

    first = client.post(
        "/api/v1/pricing/catalog/PRC000001/approve",
        json={
            "approved_price": 399.99,
            "approved_by": "Ryan Brown",
        },
    )

    assert first.status_code == 200

    second = client.post(
        "/api/v1/pricing/catalog/PRC000001/approve",
        json={
            "approved_price": 389.99,
            "approved_by": "Ryan Brown",
        },
    )

    assert second.status_code == 409


@pytest.mark.parametrize(
    "approved_price",
    [
        0,
        -1.00,
    ],
)
def test_approval_rejects_invalid_price(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
    approved_price: float,
) -> None:
    client, _ = pricing_catalog_client

    save_pricing_record(client)

    response = client.post(
        "/api/v1/pricing/catalog/PRC000001/approve",
        json={
            "approved_price": approved_price,
            "approved_by": "Ryan Brown",
        },
    )

    assert response.status_code == 422


def test_approval_requires_approver(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = pricing_catalog_client

    save_pricing_record(client)

    response = client.post(
        "/api/v1/pricing/catalog/PRC000001/approve",
        json={
            "approved_price": 399.99,
            "approved_by": "   ",
        },
    )

    assert response.status_code == 422


def test_catalog_save_fails_closed_without_rule(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = pricing_catalog_client

    monkeypatch.setattr(
        api_app_module,
        "get_pricing_rule_provider",
        lambda: PricingRuleProvider(),
    )

    response = client.post(
        "/api/v1/pricing/catalog",
        json={
            "device_id": "DEV000093",
            "service_type_id": "STY000001",
            "supplier_product_id": "249690",
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "No approved runtime pricing rule is available for STY000001."
    )


def test_approved_catalog_record_cannot_be_refreshed(
    pricing_catalog_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, database = pricing_catalog_client

    save_pricing_record(client)

    approval = client.post(
        "/api/v1/pricing/catalog/PRC000001/approve",
        json={
            "approved_price": 399.99,
            "approved_by": "Ryan Brown",
        },
    )

    assert approval.status_code == 200

    refresh = client.post(
        "/api/v1/pricing/catalog",
        json={
            "device_id": "DEV000093",
            "service_type_id": "STY000001",
            "variant_key": "BASE",
            "supplier_product_id": "249690",
            "shipping": 10.00,
            "consumables": 5.00,
        },
    )

    assert refresh.status_code == 409

    assert refresh.json()["detail"] == (
        "Approved pricing records cannot be refreshed. "
        "A new pricing revision is required."
    )

    stored = database.get_service_pricing_record("PRC000001")

    assert stored is not None
    assert stored["approval_status"] == "APPROVED"
    assert stored["approved_price_cents"] == 39999
