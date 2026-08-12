from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from desktop.services.payment_service import PaymentService


@pytest.fixture
def payment_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> PaymentService:
    database_path = tmp_path / "test_operations.sqlite3"

    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE repair_tickets (
                ticket_id TEXT PRIMARY KEY
            )
            """)

        connection.execute(
            """
            INSERT INTO repair_tickets (
                ticket_id
            )
            VALUES (?)
            """,
            ("RPR000001",),
        )

        connection.commit()

    monkeypatch.setattr(
        PaymentService,
        "_resolve_database_path",
        staticmethod(lambda: database_path),
    )

    return PaymentService()


def test_record_square_refund_is_idempotent(
    payment_service: PaymentService,
) -> None:
    first = payment_service.record_square_refund(
        "RPR000001",
        amount=10.00,
        square_payment_id="SQPAY001",
        square_refund_id="SQREF001",
    )

    second = payment_service.record_square_refund(
        "RPR000001",
        amount=10.00,
        square_payment_id="SQPAY001",
        square_refund_id="SQREF001",
    )

    assert first["payment_id"] == second["payment_id"]
    assert first["square_refund_id"] == "SQREF001"
    assert first["refunded_square_payment_id"] == "SQPAY001"

    refunds = [
        payment
        for payment in payment_service.list_repair_payments("RPR000001")
        if payment["payment_method"] == "Square Refund"
    ]

    assert len(refunds) == 1


def test_refunded_amount_ignores_duplicate_legacy_refund(
    payment_service: PaymentService,
) -> None:
    payment_service.create_payment(
        "RPR000001",
        {
            "payment_method": "Square Refund",
            "payment_status": "Partially Refunded",
            "amount": 5.00,
            "reference_number": "LEGACY-REFUND-001",
            "refunded_square_payment_id": "SQPAY001",
        },
    )

    payment_service.create_payment(
        "RPR000001",
        {
            "payment_method": "Square Refund",
            "payment_status": "Partially Refunded",
            "amount": 5.00,
            "reference_number": "LEGACY-REFUND-001",
            "refunded_square_payment_id": "SQPAY001",
        },
    )

    refunded = payment_service.refunded_amount_for_square_payment(
        "RPR000001",
        "SQPAY001",
    )

    assert refunded == 5.00


def test_refunded_amount_counts_distinct_refunds(
    payment_service: PaymentService,
) -> None:
    payment_service.record_square_refund(
        "RPR000001",
        amount=5.00,
        square_payment_id="SQPAY001",
        square_refund_id="SQREF001",
    )

    payment_service.record_square_refund(
        "RPR000001",
        amount=7.00,
        square_payment_id="SQPAY001",
        square_refund_id="SQREF002",
    )

    refunded = payment_service.refunded_amount_for_square_payment(
        "RPR000001",
        "SQPAY001",
    )

    assert refunded == 12.00


def test_payment_operation_persists(
    payment_service: PaymentService,
) -> None:
    operation = payment_service.create_payment_operation(
        "RPR000001",
        operation_type="TERMINAL_PAYMENT",
        operation_status="PENDING",
        amount=25.00,
        square_terminal_checkout_id="CHECKOUT001",
    )

    loaded = payment_service.get_payment_operation(operation["operation_id"])

    assert loaded is not None
    assert loaded["repair_id"] == "RPR000001"
    assert loaded["operation_type"] == "TERMINAL_PAYMENT"
    assert loaded["operation_status"] == "PENDING"
    assert loaded["square_terminal_checkout_id"] == "CHECKOUT001"


def test_completed_operation_is_not_pending(
    payment_service: PaymentService,
) -> None:
    operation = payment_service.create_payment_operation(
        "RPR000001",
        operation_type="SQUARE_REFUND",
        operation_status="PENDING",
        amount=5.00,
        square_payment_id="SQPAY001",
        square_refund_id="SQREF001",
    )

    payment_service.update_payment_operation(
        operation["operation_id"],
        operation_status="COMPLETED",
        completed=True,
    )

    pending = payment_service.list_pending_payment_operations("RPR000001")

    assert pending == []


def test_schema_backfills_unique_legacy_refund(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "legacy_unique.sqlite3"

    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE repair_tickets (
                ticket_id TEXT PRIMARY KEY
            )
            """)

        connection.execute(
            """
            INSERT INTO repair_tickets (
                ticket_id
            )
            VALUES (?)
            """,
            ("RPR000001",),
        )

        connection.execute("""
            CREATE TABLE repair_payments (
                payment_id TEXT PRIMARY KEY,
                repair_id TEXT NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'Completed',
                payment_method TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                payment_timestamp TEXT NOT NULL,
                reference_number TEXT,
                square_payment_id TEXT,
                square_order_id TEXT,
                square_terminal_checkout_id TEXT,
                square_receipt_url TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL DEFAULT 'Ryan Brown'
            )
            """)

        connection.execute(
            """
            INSERT INTO repair_payments (
                payment_id,
                repair_id,
                payment_status,
                payment_method,
                amount,
                currency,
                payment_timestamp,
                reference_number,
                notes,
                created_at,
                created_by
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
            """,
            (
                "PAY000001",
                "RPR000001",
                "Partially Refunded",
                "Square Refund",
                5.00,
                "USD",
                "2026-08-01T00:00:00+00:00",
                "LEGACY-REFUND-001",
                "Square refund for SQPAY001.",
                "2026-08-01T00:00:00+00:00",
                "Ryan Brown",
            ),
        )

        connection.commit()

    monkeypatch.setattr(
        PaymentService,
        "_resolve_database_path",
        staticmethod(lambda: database_path),
    )

    service = PaymentService()

    with service.connect() as connection:
        row = connection.execute(
            """
            SELECT
                square_refund_id,
                refunded_square_payment_id
            FROM repair_payments
            WHERE payment_id = ?
            """,
            ("PAY000001",),
        ).fetchone()

    assert row is not None
    assert row["square_refund_id"] == "LEGACY-REFUND-001"
    assert row["refunded_square_payment_id"] == "SQPAY001"


def test_schema_leaves_duplicate_legacy_refund_ids_unassigned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "legacy_duplicate.sqlite3"

    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE repair_tickets (
                ticket_id TEXT PRIMARY KEY
            )
            """)

        connection.execute(
            """
            INSERT INTO repair_tickets (
                ticket_id
            )
            VALUES (?)
            """,
            ("RPR000001",),
        )

        connection.execute("""
            CREATE TABLE repair_payments (
                payment_id TEXT PRIMARY KEY,
                repair_id TEXT NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'Completed',
                payment_method TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                payment_timestamp TEXT NOT NULL,
                reference_number TEXT,
                square_payment_id TEXT,
                square_order_id TEXT,
                square_terminal_checkout_id TEXT,
                square_receipt_url TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL DEFAULT 'Ryan Brown'
            )
            """)

        for payment_id in (
            "PAY000001",
            "PAY000002",
        ):
            connection.execute(
                """
                INSERT INTO repair_payments (
                    payment_id,
                    repair_id,
                    payment_status,
                    payment_method,
                    amount,
                    currency,
                    payment_timestamp,
                    reference_number,
                    notes,
                    created_at,
                    created_by
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """,
                (
                    payment_id,
                    "RPR000001",
                    "Partially Refunded",
                    "Square Refund",
                    5.00,
                    "USD",
                    "2026-08-01T00:00:00+00:00",
                    "LEGACY-DUPLICATE-001",
                    "Square refund for SQPAY001.",
                    "2026-08-01T00:00:00+00:00",
                    "Ryan Brown",
                ),
            )

        connection.commit()

    monkeypatch.setattr(
        PaymentService,
        "_resolve_database_path",
        staticmethod(lambda: database_path),
    )

    service = PaymentService()

    with service.connect() as connection:
        rows = connection.execute("""
            SELECT
                square_refund_id,
                refunded_square_payment_id
            FROM repair_payments
            ORDER BY payment_id
            """).fetchall()

    assert len(rows) == 2

    assert all(row["square_refund_id"] is None for row in rows)

    assert all(row["refunded_square_payment_id"] == "SQPAY001" for row in rows)
