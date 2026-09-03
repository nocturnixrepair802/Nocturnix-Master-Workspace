from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from persistence.operations_db import OperationsDatabase


def pricing_record(
    *,
    pricing_record_id: str = "PRC000001",
    catalog_device_id: str = "DEV000093",
    service_type_id: str = "STY000001",
    variant_key: str = "BASE",
    supplier_product_id: str = "249690",
) -> dict[str, object]:
    return {
        "pricing_record_id": pricing_record_id,
        "catalog_device_id": catalog_device_id,
        "service_type_id": service_type_id,
        "service_type": "Screen Replacement",
        "service_category_id": "SC000010",
        "variant_key": variant_key,
        "variant_name": None,
        "supplier": "Mobile Sentrix",
        "supplier_product_id": supplier_product_id,
        "supplier_sku": "107082999999",
        "part_name": "OLED Screen Assembly",
        "part_cost_cents": 4500,
        "supplier_in_stock": 1,
        "supplier_stock_qty": 12,
        "supplier_observed_at": "2026-09-03T18:00:00Z",
        "default_labor_hours": "1.00",
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
        "shipping_cents": 0,
        "consumables_cents": 500,
        "base_direct_cost_cents": 15000,
        "total_internal_cost_cents": 18600,
        "recommended_price_cents": 26599,
        "gross_profit_cents": 7999,
        "gross_margin": "0.300827",
        "pricing_status": "READY",
        "approved_price_cents": None,
        "approval_status": "DRAFT",
        "approved_at": None,
        "approved_by": None,
        "created_at": "2026-09-03T18:00:00Z",
        "updated_at": "2026-09-03T18:00:00Z",
    }


def test_initialize_creates_service_pricing_catalog(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "operations.sqlite3"

    OperationsDatabase(database_path)

    with sqlite3.connect(database_path) as connection:
        row = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'service_pricing_catalog'
            """).fetchone()

    assert row is not None


def test_next_service_pricing_id(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    assert (
        database.next_id(
            table="service_pricing_catalog",
            column="pricing_record_id",
            prefix="PRC",
            width=6,
        )
        == "PRC000001"
    )

    database.create_service_pricing_record(pricing_record())

    assert (
        database.next_id(
            table="service_pricing_catalog",
            column="pricing_record_id",
            prefix="PRC",
            width=6,
        )
        == "PRC000002"
    )


def test_create_and_get_service_pricing_record(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    record = pricing_record()

    created = database.create_service_pricing_record(record)

    assert created == record

    stored = database.get_service_pricing_record("PRC000001")

    assert stored is not None
    assert stored["catalog_device_id"] == "DEV000093"
    assert stored["service_type_id"] == "STY000001"
    assert stored["variant_key"] == "BASE"
    assert stored["supplier_product_id"] == "249690"
    assert stored["recommended_price_cents"] == 26599
    assert stored["approval_status"] == "DRAFT"


def test_list_service_pricing_records_filters(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    database.create_service_pricing_record(pricing_record())

    database.create_service_pricing_record(
        pricing_record(
            pricing_record_id="PRC000002",
            service_type_id="STY000055",
            variant_key="ADVANCED_DIAGNOSTIC",
            supplier_product_id="249691",
        )
    )

    records = database.list_service_pricing_records(
        service_type_id="STY000055",
        variant_key="advanced_diagnostic",
    )

    assert len(records) == 1
    assert records[0]["pricing_record_id"] == "PRC000002"


def test_duplicate_catalog_identity_is_rejected(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    database.create_service_pricing_record(pricing_record())

    duplicate = pricing_record(pricing_record_id="PRC000002")

    with pytest.raises(
        sqlite3.IntegrityError,
    ):
        database.create_service_pricing_record(duplicate)


def test_same_service_can_have_distinct_variant(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    database.create_service_pricing_record(
        pricing_record(
            service_type_id="STY000055",
            variant_key="BASE",
        )
    )

    database.create_service_pricing_record(
        pricing_record(
            pricing_record_id="PRC000002",
            service_type_id="STY000055",
            variant_key="ADVANCED_DIAGNOSTIC",
        )
    )

    records = database.list_service_pricing_records(
        service_type_id="STY000055",
    )

    assert len(records) == 2
