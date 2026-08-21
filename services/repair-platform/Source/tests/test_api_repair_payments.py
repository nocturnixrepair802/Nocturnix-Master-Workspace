from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

import api.app as api_app


class FakeOperationsDatabase:
    def get_repair(
        self,
        repair_id: str,
    ) -> dict[str, Any] | None:
        if repair_id == "MISSING":
            return None

        return {
            "ticket_id": repair_id,
            "repair_status": "In Repair",
            "final_cost": 200.0,
        }

    def list_repair_payments(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        return [
            {
                "payment_id": "PAY000002",
                "repair_id": repair_id,
                "payment_status": "Completed",
                "payment_method": "Square",
                "amount": 75.0,
                "currency": "USD",
                "payment_timestamp": ("2026-08-12T14:00:00+00:00"),
                "reference_number": "REF002",
                "square_payment_id": "SQPAY002",
                "square_order_id": "",
                "square_terminal_checkout_id": "",
                "square_receipt_url": "",
                "square_refund_id": "",
                "refunded_square_payment_id": "",
                "notes": "",
                "created_at": ("2026-08-12T14:00:00+00:00"),
                "created_by": "Ryan Brown",
            },
            {
                "payment_id": "PAY000001",
                "repair_id": repair_id,
                "payment_status": "Completed",
                "payment_method": "Cash",
                "amount": 50.0,
                "currency": "USD",
                "payment_timestamp": ("2026-08-12T13:00:00+00:00"),
                "reference_number": "REF001",
                "square_payment_id": "",
                "square_order_id": "",
                "square_terminal_checkout_id": "",
                "square_receipt_url": "",
                "square_refund_id": "",
                "refunded_square_payment_id": "",
                "notes": "Deposit",
                "created_at": ("2026-08-12T13:00:00+00:00"),
                "created_by": "Ryan Brown",
            },
        ]

    def repair_payment_summary(
        self,
        repair_id: str,
    ) -> dict[str, Any] | None:
        if repair_id == "MISSING":
            return None

        return {
            "repair_id": repair_id,
            "repair_status": "In Repair",
            "final_cost": 200.0,
            "amount_paid": 125.0,
            "balance_due": 75.0,
            "payment_status": "Partially Paid",
            "currency": "USD",
        }


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    monkeypatch.setattr(
        api_app,
        "_database",
        FakeOperationsDatabase(),
    )

    return TestClient(api_app.app)


def test_repair_payments_returns_payment_history(
    client: TestClient,
) -> None:
    response = client.get("/api/repairs/RPR000100/payments")

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 2

    assert payload[0]["payment_id"] == ("PAY000002")
    assert payload[0]["repair_id"] == ("RPR000100")
    assert payload[0]["payment_method"] == ("Square")
    assert payload[0]["amount"] == 75.0
    assert payload[0]["square_payment_id"] == ("SQPAY002")

    assert payload[1]["payment_id"] == ("PAY000001")
    assert payload[1]["payment_method"] == ("Cash")
    assert payload[1]["amount"] == 50.0


def test_repair_payments_returns_404_when_repair_missing(
    client: TestClient,
) -> None:
    response = client.get("/api/repairs/MISSING/payments")

    assert response.status_code == 404

    assert response.json() == {"detail": "Repair ticket not found."}


def test_repair_payment_summary_returns_totals(
    client: TestClient,
) -> None:
    response = client.get("/api/repairs/RPR000100/payments/summary")

    assert response.status_code == 200

    payload = response.json()

    assert payload == {
        "repair_id": "RPR000100",
        "repair_status": "In Repair",
        "final_cost": 200.0,
        "amount_paid": 125.0,
        "balance_due": 75.0,
        "payment_status": "Partially Paid",
        "currency": "USD",
    }


def test_repair_payment_summary_returns_404_when_missing(
    client: TestClient,
) -> None:
    response = client.get("/api/repairs/MISSING/payments/summary")

    assert response.status_code == 404

    assert response.json() == {"detail": "Repair ticket not found."}
