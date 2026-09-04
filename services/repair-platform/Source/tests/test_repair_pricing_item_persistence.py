from __future__ import annotations

from pathlib import Path

from persistence.operations_db import OperationsDatabase


def create_customer_repair_prerequisites(
    database: OperationsDatabase,
) -> None:
    database.create_customer(
        {
            "customer_id": "CUS000001",
            "customer_type": "Individual",
            "first_name": "Test",
            "last_name": "Customer",
            "business_name": "",
            "email": "",
            "mobile_phone": "",
            "home_phone": "",
            "work_phone": "",
            "preferred_contact": "Mobile Phone",
            "billing_address": "",
            "shipping_address": "",
            "tax_exempt": 0,
            "active": 1,
            "date_created": "2026-09-04T00:00:00Z",
            "last_modified": "2026-09-04T00:00:00Z",
            "notes": "",
        }
    )

    database.create_customer_device(
        {
            "device_id": "CDEV000001",
            "customer_id": "CUS000001",
            "catalog_device_id": "DEV000093",
            "manufacturer": "Apple",
            "device_family": "iPhone",
            "device_model": "iPhone 13 Pro",
            "serial_number": "",
            "imei_service_tag": "",
            "color": "",
            "storage": "",
            "carrier": "",
            "purchase_date": None,
            "warranty_expiration": None,
            "active": 1,
            "notes": "",
        }
    )

    database.create_repair(
        {
            "ticket_id": "RPR000001",
            "customer_id": "CUS000001",
            "device_id": "CDEV000001",
            "repair_status": "New Intake",
            "intake_date": "2026-09-04T00:00:00Z",
            "technician": "Ryan Brown",
            "priority": "Normal",
            "due_date": "",
            "problem_description": "Cracked screen",
            "diagnosis": "",
            "estimated_cost": None,
            "final_cost": None,
            "date_completed": None,
            "date_picked_up": None,
            "warranty": 0,
            "notes": "",
            "last_modified": "2026-09-04T00:00:00Z",
        }
    )


def create_approved_pricing_record(
    database: OperationsDatabase,
) -> None:
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
            "approved_price_cents": 26999,
            "approval_status": "APPROVED",
            "approved_at": "2026-09-04T00:00:00Z",
            "approved_by": "Ryan Brown",
            "created_at": "2026-09-04T00:00:00Z",
            "updated_at": "2026-09-04T00:00:00Z",
        }
    )


def test_next_repair_pricing_item_id(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    result = database.next_id(
        table="repair_pricing_items",
        column="repair_pricing_item_id",
        prefix="RPI",
        width=6,
    )

    assert result == "RPI000001"


def test_create_get_and_list_repair_pricing_item(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)
    create_approved_pricing_record(database)

    record = {
        "repair_pricing_item_id": "RPI000001",
        "repair_id": "RPR000001",
        "pricing_record_id": "PRC000001",
        "service_type_id": "STY000001",
        "variant_key": "BASE",
        "service_type": "Screen Replacement",
        "quality_class": "REFURBISHED_OEM",
        "customer_facing_tier": "PREFERRED",
        "supplier": "Mobile Sentrix",
        "supplier_product_id": "123078",
        "supplier_sku": "107082080528",
        "part_name": "OLED Assembly For iPhone 13 Pro (Refurbished)",
        "quoted_unit_price_cents": 26999,
        "quantity": 1,
        "line_total_cents": 26999,
        "pricing_snapshot_at": "2026-09-04T00:00:00Z",
        "created_at": "2026-09-04T00:00:00Z",
        "updated_at": "2026-09-04T00:00:00Z",
    }

    created = database.create_repair_pricing_item(record)

    assert created == record

    stored = database.get_repair_pricing_item("RPI000001")

    assert stored is not None
    assert stored["repair_id"] == "RPR000001"
    assert stored["pricing_record_id"] == "PRC000001"
    assert stored["quality_class"] == "REFURBISHED_OEM"
    assert stored["quoted_unit_price_cents"] == 26999
    assert stored["line_total_cents"] == 26999

    listed = database.list_repair_pricing_items("RPR000001")

    assert len(listed) == 1
    assert listed[0]["repair_pricing_item_id"] == "RPI000001"


def test_delete_repair_pricing_item(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_customer_repair_prerequisites(database)
    create_approved_pricing_record(database)

    database.create_repair_pricing_item(
        {
            "repair_pricing_item_id": "RPI000001",
            "repair_id": "RPR000001",
            "pricing_record_id": "PRC000001",
            "service_type_id": "STY000001",
            "variant_key": "BASE",
            "service_type": "Screen Replacement",
            "quality_class": "REFURBISHED_OEM",
            "customer_facing_tier": "PREFERRED",
            "supplier": "Mobile Sentrix",
            "supplier_product_id": "123078",
            "supplier_sku": "107082080528",
            "part_name": "OLED Assembly For iPhone 13 Pro (Refurbished)",
            "quoted_unit_price_cents": 26999,
            "quantity": 1,
            "line_total_cents": 26999,
            "pricing_snapshot_at": "2026-09-04T00:00:00Z",
            "created_at": "2026-09-04T00:00:00Z",
            "updated_at": "2026-09-04T00:00:00Z",
        }
    )

    assert database.delete_repair_pricing_item("RPI000001") is True
    assert database.get_repair_pricing_item("RPI000001") is None
    assert database.delete_repair_pricing_item("RPI000001") is False
