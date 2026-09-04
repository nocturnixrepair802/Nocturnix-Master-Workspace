from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import app as api_app_module
from api.app import app
from persistence.operations_db import OperationsDatabase
from services.repair_pricing_service import RepairPricingService
from tests.test_repair_pricing_item_persistence import (
    create_approved_pricing_record,
    create_customer_repair_prerequisites,
)


@pytest.fixture
def repair_pricing_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, OperationsDatabase]]:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)
    create_approved_pricing_record(database)
    monkeypatch.setattr(
        api_app_module,
        "get_database",
        lambda: database,
    )

    app.dependency_overrides[api_app_module.get_repair_pricing_service] = lambda: (
        RepairPricingService(
            operations_database=database,
        )
    )

    client = TestClient(app)

    try:
        yield client, database

    finally:
        app.dependency_overrides.clear()


def test_select_repair_pricing_item(
    repair_pricing_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, database = repair_pricing_client

    response = client.post(
        "/api/repairs/RPR000001/pricing-items",
        json={
            "pricing_record_id": "PRC000001",
            "quantity": 1,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["repair_pricing_item_id"] == "RPI000001"
    assert payload["repair_id"] == "RPR000001"
    assert payload["pricing_record_id"] == "PRC000001"

    assert payload["service_type_id"] == "STY000001"
    assert payload["service_type"] == "Screen Replacement"

    assert payload["quality_class"] == "REFURBISHED_OEM"
    assert payload["customer_facing_tier"] == "PREFERRED"

    assert payload["supplier"] == "Mobile Sentrix"
    assert payload["supplier_product_id"] == "123078"
    assert payload["supplier_sku"] == "107082080528"

    assert payload["quoted_unit_price_cents"] == 26999
    assert payload["quantity"] == 1
    assert payload["line_total_cents"] == 26999

    stored = database.get_repair_pricing_item("RPI000001")

    assert stored is not None
    assert stored["pricing_record_id"] == "PRC000001"
    assert stored["quoted_unit_price_cents"] == 26999


def test_list_repair_pricing_items(
    repair_pricing_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_pricing_client

    selection = client.post(
        "/api/repairs/RPR000001/pricing-items",
        json={
            "pricing_record_id": "PRC000001",
            "quantity": 1,
        },
    )

    assert selection.status_code == 200

    response = client.get("/api/repairs/RPR000001/pricing-items")

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["repair_pricing_item_id"] == "RPI000001"
    assert payload[0]["pricing_record_id"] == "PRC000001"
    assert payload[0]["quoted_unit_price_cents"] == 26999


def test_select_repair_pricing_item_rejects_invalid_quantity(
    repair_pricing_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_pricing_client

    response = client.post(
        "/api/repairs/RPR000001/pricing-items",
        json={
            "pricing_record_id": "PRC000001",
            "quantity": 0,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == ("quantity must be greater than zero.")


def test_select_repair_pricing_item_unknown_repair(
    repair_pricing_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_pricing_client

    response = client.post(
        "/api/repairs/RPR999999/pricing-items",
        json={
            "pricing_record_id": "PRC000001",
            "quantity": 1,
        },
    )

    assert response.status_code == 404


def test_list_repair_pricing_items_unknown_repair(
    repair_pricing_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_pricing_client

    response = client.get("/api/repairs/RPR999999/pricing-items")

    assert response.status_code == 404


def test_repair_workspace_includes_pricing_items(
    repair_pricing_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_pricing_client

    selection = client.post(
        "/api/repairs/RPR000001/pricing-items",
        json={
            "pricing_record_id": "PRC000001",
            "quantity": 1,
        },
    )

    assert selection.status_code == 200

    response = client.get("/api/repairs/RPR000001/workspace")

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == "RPR000001"
    assert payload["catalog_device_id"] == "DEV000093"

    assert payload["quoted_total_cents"] == 26999

    assert len(payload["pricing_items"]) == 1

    pricing_item = payload["pricing_items"][0]

    assert pricing_item["repair_pricing_item_id"] == "RPI000001"
    assert pricing_item["pricing_record_id"] == "PRC000001"
    assert pricing_item["service_type_id"] == "STY000001"
    assert pricing_item["quality_class"] == "REFURBISHED_OEM"
    assert pricing_item["customer_facing_tier"] == "PREFERRED"
    assert pricing_item["quoted_unit_price_cents"] == 26999
    assert pricing_item["line_total_cents"] == 26999
