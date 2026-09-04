from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from persistence.operations_db import OperationsDatabase
from services.repair_pricing_service import (
    RepairPricingNotFoundError,
    RepairPricingService,
    RepairPricingStateError,
    RepairPricingValidationError,
)
from tests.test_repair_pricing_item_persistence import (
    create_approved_pricing_record,
    create_customer_repair_prerequisites,
)


def test_select_approved_pricing_record(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)
    create_approved_pricing_record(database)

    service = RepairPricingService(database)

    item = service.select_pricing_record(
        "RPR000001",
        "PRC000001",
        quantity=1,
        now=datetime(
            2026,
            9,
            4,
            1,
            30,
            tzinfo=UTC,
        ),
    )

    assert item["repair_pricing_item_id"] == "RPI000001"
    assert item["repair_id"] == "RPR000001"
    assert item["pricing_record_id"] == "PRC000001"
    assert item["service_type_id"] == "STY000001"
    assert item["quality_class"] == "REFURBISHED_OEM"
    assert item["customer_facing_tier"] == "PREFERRED"
    assert item["quoted_unit_price_cents"] == 26999
    assert item["quantity"] == 1
    assert item["line_total_cents"] == 26999


def test_select_pricing_record_requires_approved_record(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)

    database.create_service_pricing_record(
        {
            "pricing_record_id": "PRC000001",
            "catalog_device_id": "DEV000093",
            "service_type_id": "STY000001",
            "service_type": "Screen Replacement",
            "service_category_id": "SC000010",
            "variant_key": "BASE",
            "variant_name": None,
            "supplier": "Mobile Sentrix",
            "supplier_product_id": "123078",
            "supplier_sku": "107082080528",
            "part_name": "OLED Assembly For iPhone 13 Pro (Refurbished)",
            "quality_class": "REFURBISHED_OEM",
            "quality_rank": 3,
            "customer_facing_tier": "PREFERRED",
            "commercial_selection_status": "PREFERRED",
            "recommended_action": "USE",
            "part_cost_cents": 11460,
            "supplier_in_stock": 1,
            "supplier_stock_qty": 7,
            "supplier_observed_at": "2026-09-04T00:00:00Z",
            "default_labor_hours": "1.0",
            "labor_profile_id": "LAB000002",
            "labor_tier": "L2 Standard",
            "hourly_rate_cents": 10000,
            "minimum_charge_cents": 8500,
            "target_margin": "0.30",
            "minimum_margin": "0.20",
            "overhead_rate": "0.12",
            "warranty_rate": "0.05",
            "risk_rate": "0.04",
            "processing_rate": "0.03",
            "rounding_rule": "End in .99",
            "billable_labor_cost_cents": 10000,
            "shipping_cents": 500,
            "consumables_cents": 500,
            "base_direct_cost_cents": 22460,
            "total_internal_cost_cents": 27850,
            "recommended_price_cents": 39799,
            "gross_profit_cents": 11949,
            "gross_margin": "0.3002",
            "pricing_status": "READY",
            "approved_price_cents": None,
            "approval_status": "DRAFT",
            "approved_at": None,
            "approved_by": None,
            "created_at": "2026-09-04T00:00:00Z",
            "updated_at": "2026-09-04T00:00:00Z",
        }
    )

    service = RepairPricingService(database)

    with pytest.raises(
        RepairPricingStateError,
        match="is not APPROVED",
    ):
        service.select_pricing_record(
            "RPR000001",
            "PRC000001",
        )


def test_select_pricing_record_rejects_invalid_quantity(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)
    create_approved_pricing_record(database)

    service = RepairPricingService(database)

    with pytest.raises(
        RepairPricingValidationError,
        match="quantity must be greater than zero",
    ):
        service.select_pricing_record(
            "RPR000001",
            "PRC000001",
            quantity=0,
        )


def test_select_pricing_record_rejects_unknown_repair(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_approved_pricing_record(database)

    service = RepairPricingService(database)

    with pytest.raises(
        RepairPricingNotFoundError,
        match="Repair 'RPR999999' was not found",
    ):
        service.select_pricing_record(
            "RPR999999",
            "PRC000001",
        )


def test_select_pricing_record_rejects_unknown_pricing_record(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)

    service = RepairPricingService(database)

    with pytest.raises(
        RepairPricingNotFoundError,
        match="Pricing record 'PRC999999' was not found",
    ):
        service.select_pricing_record(
            "RPR000001",
            "PRC999999",
        )


def test_select_pricing_record_requires_approved_price(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)
    create_approved_pricing_record(database)

    with database.connect() as connection:
        connection.execute(
            """
            UPDATE service_pricing_catalog
            SET approved_price_cents = NULL
            WHERE pricing_record_id = ?
            """,
            ("PRC000001",),
        )

    service = RepairPricingService(database)

    with pytest.raises(
        RepairPricingStateError,
        match="does not have an approved price",
    ):
        service.select_pricing_record(
            "RPR000001",
            "PRC000001",
        )


def test_selected_repair_pricing_item_preserves_snapshot(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)
    create_approved_pricing_record(database)

    service = RepairPricingService(database)

    selected = service.select_pricing_record(
        "RPR000001",
        "PRC000001",
        now=datetime(
            2026,
            9,
            4,
            2,
            0,
            tzinfo=UTC,
        ),
    )

    assert selected["quoted_unit_price_cents"] == 26999
    assert selected["quality_class"] == "REFURBISHED_OEM"
    assert selected["customer_facing_tier"] == "PREFERRED"
    assert selected["supplier_sku"] == "107082080528"

    with database.connect() as connection:
        connection.execute(
            """
            UPDATE service_pricing_catalog
            SET approved_price_cents = ?,
                quality_class = ?,
                customer_facing_tier = ?,
                supplier_sku = ?
            WHERE pricing_record_id = ?
            """,
            (
                29999,
                "CHANGED_QUALITY",
                "CHANGED_TIER",
                "CHANGED_SKU",
                "PRC000001",
            ),
        )

    stored_item = database.get_repair_pricing_item("RPI000001")

    assert stored_item is not None
    assert stored_item["quoted_unit_price_cents"] == 26999
    assert stored_item["quality_class"] == "REFURBISHED_OEM"
    assert stored_item["customer_facing_tier"] == "PREFERRED"
    assert stored_item["supplier_sku"] == "107082080528"


def test_select_pricing_record_rejects_different_device(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)
    create_approved_pricing_record(database)

    with database.connect() as connection:
        connection.execute(
            """
            UPDATE service_pricing_catalog
            SET catalog_device_id = ?
            WHERE pricing_record_id = ?
            """,
            (
                "DEV000094",
                "PRC000001",
            ),
        )

    service = RepairPricingService(database)

    with pytest.raises(
        RepairPricingStateError,
        match="is for catalog device 'DEV000094', not repair device 'DEV000093'",
    ):
        service.select_pricing_record(
            "RPR000001",
            "PRC000001",
        )
