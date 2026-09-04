from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from persistence.operations_db import OperationsDatabase
from tests.test_repair_pricing_item_persistence import (
    create_approved_pricing_record,
    create_customer_repair_prerequisites,
)


def create_repair_pricing_item(
    database: OperationsDatabase,
) -> None:
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
            "pricing_snapshot_at": "2026-09-04T02:30:00Z",
            "created_at": "2026-09-04T02:30:00Z",
            "updated_at": "2026-09-04T02:30:00Z",
        }
    )


def test_next_repair_authorization_id(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    result = database.next_id(
        table="repair_authorizations",
        column="authorization_id",
        prefix="AUT",
        width=6,
    )

    assert result == "AUT000001"


def test_create_get_and_list_repair_authorization(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    record = {
        "authorization_id": "AUT000001",
        "repair_id": "RPR000001",
        "authorization_type": "REPAIR_QUOTE",
        "authorization_status": "PENDING",
        "quoted_total_cents": 26999,
        "currency": "USD",
        "terms_document_id": "",
        "terms_version": "",
        "customer_name": "",
        "authorization_method": "",
        "authorized_at": None,
        "declined_at": None,
        "created_at": "2026-09-04T02:35:00Z",
        "updated_at": "2026-09-04T02:35:00Z",
        "created_by": "Ryan Brown",
    }

    created = database.create_repair_authorization(
        record,
        ["RPI000001"],
    )

    assert created == record

    stored = database.get_repair_authorization("AUT000001")

    assert stored is not None
    assert stored["repair_id"] == "RPR000001"
    assert stored["authorization_status"] == "PENDING"
    assert stored["quoted_total_cents"] == 26999

    listed = database.list_repair_authorizations("RPR000001")

    assert len(listed) == 1
    assert listed[0]["authorization_id"] == "AUT000001"

    items = database.list_repair_authorization_items("AUT000001")

    assert len(items) == 1
    assert items[0]["authorization_id"] == "AUT000001"
    assert items[0]["repair_pricing_item_id"] == "RPI000001"


def test_create_repair_authorization_rolls_back_on_invalid_item(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    record = {
        "authorization_id": "AUT000001",
        "repair_id": "RPR000001",
        "authorization_type": "REPAIR_QUOTE",
        "authorization_status": "PENDING",
        "quoted_total_cents": 26999,
        "currency": "USD",
        "terms_document_id": "",
        "terms_version": "",
        "customer_name": "",
        "authorization_method": "",
        "authorized_at": None,
        "declined_at": None,
        "created_at": "2026-09-04T02:35:00Z",
        "updated_at": "2026-09-04T02:35:00Z",
        "created_by": "Ryan Brown",
    }

    with pytest.raises(sqlite3.IntegrityError):
        database.create_repair_authorization(
            record,
            ["RPI999999"],
        )

    assert database.get_repair_authorization("AUT000001") is None
