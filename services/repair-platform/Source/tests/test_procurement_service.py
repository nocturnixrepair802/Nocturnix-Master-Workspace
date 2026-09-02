from __future__ import annotations

import sys
from pathlib import Path

import pytest

SOURCE_DIR = Path(__file__).resolve().parents[1]

if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SOURCE_DIR),
    )

from services.procurement_service import (
    ProcurementNotFoundError,
    ProcurementService,
    ProcurementStateError,
    ProcurementValidationError,
)


@pytest.fixture()
def procurement_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> ProcurementService:
    database_path = tmp_path / "operations.sqlite3"

    # ProcurementService normally resolves the configured Nocturnix
    # operations database through SettingsService. Tests must never
    # use the real operations database, so override path resolution
    # before constructing the service.
    monkeypatch.setattr(
        ProcurementService,
        "_resolve_database_path",
        lambda self: database_path,
    )

    service = ProcurementService()

    assert service.database_path == database_path

    with service.connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                customer_type TEXT NOT NULL DEFAULT 'Individual',
                first_name TEXT NOT NULL DEFAULT '',
                last_name TEXT NOT NULL DEFAULT '',
                business_name TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                mobile_phone TEXT NOT NULL DEFAULT '',
                home_phone TEXT NOT NULL DEFAULT '',
                work_phone TEXT NOT NULL DEFAULT '',
                preferred_contact TEXT NOT NULL DEFAULT 'Mobile Phone',
                billing_address TEXT NOT NULL DEFAULT '',
                shipping_address TEXT NOT NULL DEFAULT '',
                tax_exempt INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                date_created TEXT NOT NULL,
                last_modified TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT ''
            )
            """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS customer_devices (
                device_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                manufacturer TEXT NOT NULL DEFAULT '',
                device_family TEXT NOT NULL DEFAULT '',
                device_model TEXT NOT NULL DEFAULT '',
                serial_number TEXT NOT NULL DEFAULT '',
                imei_service_tag TEXT NOT NULL DEFAULT '',
                color TEXT NOT NULL DEFAULT '',
                storage TEXT NOT NULL DEFAULT '',
                carrier TEXT NOT NULL DEFAULT '',
                purchase_date TEXT,
                warranty_expiration TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                notes TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(customer_id)
                    REFERENCES customers(customer_id)
            )
            """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS repair_tickets (
                ticket_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                repair_status TEXT NOT NULL DEFAULT 'New Intake',
                intake_date TEXT NOT NULL,
                technician TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'Normal',
                due_date TEXT NOT NULL DEFAULT '',
                problem_description TEXT NOT NULL DEFAULT '',
                diagnosis TEXT NOT NULL DEFAULT '',
                estimated_cost REAL,
                final_cost REAL,
                date_completed TEXT,
                date_picked_up TEXT,
                warranty INTEGER NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                last_modified TEXT NOT NULL,
                FOREIGN KEY(customer_id)
                    REFERENCES customers(customer_id),
                FOREIGN KEY(device_id)
                    REFERENCES customer_devices(device_id)
            )
            """)

        connection.execute(
            """
            INSERT INTO customers (
                customer_id,
                customer_type,
                first_name,
                last_name,
                date_created,
                last_modified
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "CUS000001",
                "Individual",
                "Test",
                "Customer",
                "2026-09-01T00:00:00+00:00",
                "2026-09-01T00:00:00+00:00",
            ),
        )

        connection.execute(
            """
            INSERT INTO customer_devices (
                device_id,
                customer_id,
                manufacturer,
                device_model
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "CDEV000001",
                "CUS000001",
                "Apple",
                "iPhone 13 Pro",
            ),
        )

        connection.execute(
            """
            INSERT INTO repair_tickets (
                ticket_id,
                customer_id,
                device_id,
                repair_status,
                intake_date,
                last_modified
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "RPR000001",
                "CUS000001",
                "CDEV000001",
                "In Repair",
                "2026-09-01T00:00:00+00:00",
                "2026-09-01T00:00:00+00:00",
            ),
        )

        connection.commit()

    return service


def create_basic_procurement(
    service: ProcurementService,
) -> dict[str, object]:
    return service.create_procurement(
        "RPR000001",
        {
            "supplier": "Mobile Sentrix",
            "requested_by": "Test User",
            "notes": "Test procurement",
        },
    )


def add_basic_item(
    service: ProcurementService,
    procurement_id: str,
) -> dict[str, object]:
    return service.add_item(
        procurement_id,
        {
            "supplier": "Mobile Sentrix",
            "supplier_product_id": "249690",
            "supplier_sku": "107182127725",
            "product_name": "iHeater Pro",
            "quantity": 2,
            "unit_cost": "351.04",
            "supplier_in_stock": True,
            "supplier_stock_quantity": 3,
            "supplier_observed_at": ("2026-09-01T21:09:58+00:00"),
            "product_url": ("https://www.mobilesentrix.com/" "test-product"),
            "created_by": "Test User",
        },
    )


def test_create_procurement(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    assert procurement["procurement_id"] == "PROC000001"

    assert procurement["repair_id"] == "RPR000001"

    assert procurement["supplier"] == "Mobile Sentrix"

    assert procurement["procurement_status"] == "Pending Approval"


def test_create_procurement_requires_existing_repair(
    procurement_service: ProcurementService,
) -> None:
    with pytest.raises(ProcurementNotFoundError):
        procurement_service.create_procurement("RPR999999")


def test_add_procurement_item(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    item = add_basic_item(
        procurement_service,
        str(procurement["procurement_id"]),
    )

    assert item["procurement_item_id"] == "PRI000001"

    assert item["supplier_product_id"] == "249690"

    assert item["supplier_sku"] == "107182127725"

    assert item["quantity"] == 2

    assert item["unit_cost"] == pytest.approx(351.04)

    assert item["estimated_line_total"] == pytest.approx(702.08)

    assert item["supplier_in_stock"] == 1

    assert item["supplier_stock_quantity"] == 3


def test_approve_requires_item(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    with pytest.raises(ProcurementValidationError):
        procurement_service.approve(str(procurement["procurement_id"]))


def test_full_procurement_workflow(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    procurement_id = str(procurement["procurement_id"])

    add_basic_item(
        procurement_service,
        procurement_id,
    )

    approved = procurement_service.approve(
        procurement_id,
        approved_by="Manager",
    )

    assert approved["procurement_status"] == "Approved"

    assert approved["approved_by"] == "Manager"

    ready = procurement_service.mark_ready_for_order(procurement_id)

    assert ready["procurement_status"] == "Ready for Order"

    ordered = procurement_service.record_manual_order(
        procurement_id,
        supplier_order_id=("MS-ORDER-1001"),
        actual_supplier_cost="700.00",
        ordered_by="Manager",
    )

    assert ordered["procurement_status"] == "Ordered"

    assert ordered["supplier_order_id"] == "MS-ORDER-1001"

    assert ordered["actual_supplier_cost"] == pytest.approx(700.00)

    received = procurement_service.receive(
        procurement_id,
        received_by="Receiver",
    )

    assert received["procurement_status"] == "Received"

    items = procurement_service.list_items(procurement_id)

    assert len(items) == 1

    assert items[0]["received_quantity"] == 2


def test_reject_pending_procurement(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    procurement_id = str(procurement["procurement_id"])

    rejected = procurement_service.reject(
        procurement_id,
        rejected_by="Manager",
        reason="Not required",
    )

    assert rejected["procurement_status"] == "Rejected"

    assert rejected["rejected_by"] == "Manager"

    assert rejected["rejection_reason"] == "Not required"


def test_cancel_ready_procurement(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    procurement_id = str(procurement["procurement_id"])

    add_basic_item(
        procurement_service,
        procurement_id,
    )

    procurement_service.approve(procurement_id)

    procurement_service.mark_ready_for_order(procurement_id)

    cancelled = procurement_service.cancel(
        procurement_id,
        cancelled_by="Manager",
        reason="Repair cancelled",
    )

    assert cancelled["procurement_status"] == "Cancelled"

    assert cancelled["cancellation_reason"] == "Repair cancelled"


def test_cannot_add_item_after_approval(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    procurement_id = str(procurement["procurement_id"])

    add_basic_item(
        procurement_service,
        procurement_id,
    )

    procurement_service.approve(procurement_id)

    with pytest.raises(ProcurementStateError):
        add_basic_item(
            procurement_service,
            procurement_id,
        )


def test_cannot_order_before_ready(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    procurement_id = str(procurement["procurement_id"])

    add_basic_item(
        procurement_service,
        procurement_id,
    )

    procurement_service.approve(procurement_id)

    with pytest.raises(ProcurementStateError):
        procurement_service.record_manual_order(
            procurement_id,
            supplier_order_id="MS-100",
        )


def test_cannot_receive_before_order(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    procurement_id = str(procurement["procurement_id"])

    with pytest.raises(ProcurementStateError):
        procurement_service.receive(procurement_id)


def test_procurement_summary(
    procurement_service: ProcurementService,
) -> None:
    procurement = create_basic_procurement(procurement_service)

    procurement_id = str(procurement["procurement_id"])

    add_basic_item(
        procurement_service,
        procurement_id,
    )

    summary = procurement_service.procurement_summary(procurement_id)

    assert summary["item_count"] == 1

    assert summary["requested_units"] == 2

    assert summary["received_units"] == 0

    assert summary["estimated_total"] == pytest.approx(702.08)


def test_ids_increment(
    procurement_service: ProcurementService,
) -> None:
    first = create_basic_procurement(procurement_service)

    second = create_basic_procurement(procurement_service)

    assert first["procurement_id"] == "PROC000001"

    assert second["procurement_id"] == "PROC000002"

    first_item = add_basic_item(
        procurement_service,
        str(first["procurement_id"]),
    )

    second_item = add_basic_item(
        procurement_service,
        str(second["procurement_id"]),
    )

    assert first_item["procurement_item_id"] == "PRI000001"

    assert second_item["procurement_item_id"] == "PRI000002"
