from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

SOURCE_DIR = Path(__file__).resolve().parents[1]

if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SOURCE_DIR),
    )

import api.app as api_app_module

from api.app import app
from services.procurement_service import (
    ProcurementNotFoundError,
    ProcurementStateError,
    ProcurementValidationError,
)


class FakeProcurementService:
    def __init__(self) -> None:
        self.procurement_status = "Pending Approval"

    def _procurement(
        self,
        *,
        status: str | None = None,
    ) -> dict[str, Any]:
        current_status = status if status is not None else self.procurement_status

        return {
            "procurement_id": "PROC000001",
            "repair_id": "RPR000001",
            "supplier": "Mobile Sentrix",
            "procurement_status": current_status,
            "requested_at": "2026-09-02T03:30:00+00:00",
            "requested_by": "Test User",
            "approved_at": (
                "2026-09-02T03:31:00+00:00"
                if current_status
                in {
                    "Approved",
                    "Ready for Order",
                    "Ordered",
                    "Received",
                }
                else None
            ),
            "approved_by": (
                "Manager"
                if current_status
                in {
                    "Approved",
                    "Ready for Order",
                    "Ordered",
                    "Received",
                }
                else None
            ),
            "rejected_at": (
                "2026-09-02T03:31:00+00:00" if current_status == "Rejected" else None
            ),
            "rejected_by": ("Manager" if current_status == "Rejected" else None),
            "rejection_reason": (
                "Not required" if current_status == "Rejected" else None
            ),
            "ready_for_order_at": (
                "2026-09-02T03:32:00+00:00"
                if current_status
                in {
                    "Ready for Order",
                    "Ordered",
                    "Received",
                }
                else None
            ),
            "supplier_order_id": (
                "MS-ORDER-1001"
                if current_status
                in {
                    "Ordered",
                    "Received",
                }
                else None
            ),
            "supplier_order_date": (
                "2026-09-02T03:33:00+00:00"
                if current_status
                in {
                    "Ordered",
                    "Received",
                }
                else None
            ),
            "actual_supplier_cost": (
                351.04
                if current_status
                in {
                    "Ordered",
                    "Received",
                }
                else None
            ),
            "ordered_at": (
                "2026-09-02T03:33:00+00:00"
                if current_status
                in {
                    "Ordered",
                    "Received",
                }
                else None
            ),
            "ordered_by": (
                "Manager"
                if current_status
                in {
                    "Ordered",
                    "Received",
                }
                else None
            ),
            "received_at": (
                "2026-09-02T03:34:00+00:00" if current_status == "Received" else None
            ),
            "received_by": ("Receiver" if current_status == "Received" else None),
            "cancelled_at": (
                "2026-09-02T03:31:00+00:00" if current_status == "Cancelled" else None
            ),
            "cancelled_by": ("Manager" if current_status == "Cancelled" else None),
            "cancellation_reason": (
                "Repair cancelled" if current_status == "Cancelled" else None
            ),
            "notes": "Test procurement",
            "created_at": "2026-09-02T03:30:00+00:00",
            "created_by": "Test User",
            "updated_at": "2026-09-02T03:30:00+00:00",
        }

    def _item(
        self,
    ) -> dict[str, Any]:
        return {
            "procurement_item_id": "PRI000001",
            "procurement_id": "PROC000001",
            "repair_id": "RPR000001",
            "supplier": "Mobile Sentrix",
            "supplier_product_id": "249690",
            "supplier_sku": "107182127725",
            "product_name": "iHeater Pro",
            "product_url": ("https://example.test/product"),
            "quantity": 1,
            "unit_cost": 351.04,
            "estimated_line_total": 351.04,
            "supplier_in_stock": 1,
            "supplier_stock_quantity": 3,
            "supplier_observed_at": ("2026-09-02T03:30:00+00:00"),
            "received_quantity": 0,
            "notes": "",
            "created_at": "2026-09-02T03:30:00+00:00",
            "created_by": "Test User",
            "updated_at": "2026-09-02T03:30:00+00:00",
        }

    def create_procurement(
        self,
        repair_id: str,
        values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if repair_id == "MISSING":
            raise ProcurementNotFoundError("Repair ticket not found.")

        record = self._procurement()

        record["repair_id"] = repair_id

        if values:
            record["supplier"] = values.get("supplier") or "Mobile Sentrix"

            record["requested_by"] = values.get("requested_by") or "Test User"

            record["notes"] = values.get("notes") or ""

        return record

    def list_repair_procurements(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        if repair_id == "MISSING":
            raise ProcurementNotFoundError("Repair ticket not found.")

        record = self._procurement()
        record["repair_id"] = repair_id

        return [record]

    def get_procurement(
        self,
        procurement_id: str,
    ) -> dict[str, Any] | None:
        if procurement_id == "MISSING":
            return None

        return self._procurement()

    def add_item(
        self,
        procurement_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        if procurement_id == "MISSING":
            raise ProcurementNotFoundError("Procurement request not found.")

        if procurement_id == "LOCKED":
            raise ProcurementStateError(
                (
                    "Procurement items may only be "
                    "changed while the procurement "
                    "is Pending Approval."
                )
            )

        if not (
            values.get("supplier_product_id")
            or values.get("supplier_sku")
            or values.get("product_name")
        ):
            raise ProcurementValidationError(
                (
                    "A procurement item must include "
                    "a supplier product ID, supplier "
                    "SKU, or product name."
                )
            )

        item = self._item()

        item["procurement_id"] = procurement_id

        item["supplier_product_id"] = values.get("supplier_product_id") or None

        item["supplier_sku"] = values.get("supplier_sku") or None

        item["product_name"] = values.get("product_name") or ""

        item["quantity"] = int(
            values.get(
                "quantity",
                1,
            )
        )

        item["unit_cost"] = values.get("unit_cost")

        if item["unit_cost"] is not None:
            item["estimated_line_total"] = round(
                float(item["unit_cost"]) * int(item["quantity"]),
                2,
            )

        item["supplier_in_stock"] = values.get("supplier_in_stock")

        item["supplier_stock_quantity"] = values.get("supplier_stock_quantity")

        return item

    def list_items(
        self,
        procurement_id: str,
    ) -> list[dict[str, Any]]:
        if procurement_id == "MISSING":
            raise ProcurementNotFoundError("Procurement request not found.")

        return [self._item()]

    def procurement_summary(
        self,
        procurement_id: str,
    ) -> dict[str, Any]:
        if procurement_id == "MISSING":
            raise ProcurementNotFoundError("Procurement request not found.")

        return {
            "procurement_id": procurement_id,
            "repair_id": "RPR000001",
            "supplier": "Mobile Sentrix",
            "procurement_status": (self.procurement_status),
            "item_count": 1,
            "requested_units": 1,
            "received_units": (1 if self.procurement_status == "Received" else 0),
            "estimated_total": 351.04,
            "actual_supplier_cost": (
                351.04
                if self.procurement_status
                in {
                    "Ordered",
                    "Received",
                }
                else None
            ),
            "supplier_order_id": (
                "MS-ORDER-1001"
                if self.procurement_status
                in {
                    "Ordered",
                    "Received",
                }
                else None
            ),
        }

    def approve(
        self,
        procurement_id: str,
        *,
        approved_by: str = "",
    ) -> dict[str, Any]:
        if procurement_id == "MISSING":
            raise ProcurementNotFoundError("Procurement request not found.")

        if procurement_id == "EMPTY":
            raise ProcurementValidationError(
                (
                    "A procurement request cannot "
                    "be approved without at least "
                    "one item."
                )
            )

        if procurement_id == "LOCKED":
            raise ProcurementStateError("Invalid procurement transition.")

        self.procurement_status = "Approved"

        record = self._procurement(status="Approved")

        record["approved_by"] = approved_by or "Manager"

        return record

    def mark_ready_for_order(
        self,
        procurement_id: str,
    ) -> dict[str, Any]:
        if procurement_id == "MISSING":
            raise ProcurementNotFoundError("Procurement request not found.")

        if procurement_id == "LOCKED":
            raise ProcurementStateError("Invalid procurement transition.")

        self.procurement_status = "Ready for Order"

        return self._procurement(status="Ready for Order")

    def reject(
        self,
        procurement_id: str,
        *,
        rejected_by: str = "",
        reason: str = "",
    ) -> dict[str, Any]:
        if procurement_id == "MISSING":
            raise ProcurementNotFoundError("Procurement request not found.")

        if procurement_id == "LOCKED":
            raise ProcurementStateError("Invalid procurement transition.")

        self.procurement_status = "Rejected"

        record = self._procurement(status="Rejected")

        record["rejected_by"] = rejected_by or "Manager"

        record["rejection_reason"] = reason or "Not required"

        return record

    def record_manual_order(
        self,
        procurement_id: str,
        *,
        supplier_order_id: str,
        actual_supplier_cost: object = None,
        ordered_by: str = "",
        supplier_order_date: str = "",
    ) -> dict[str, Any]:
        if procurement_id == "MISSING":
            raise ProcurementNotFoundError("Procurement request not found.")

        if not supplier_order_id.strip():
            raise ProcurementValidationError("Supplier order ID is required.")

        if procurement_id == "LOCKED":
            raise ProcurementStateError("Invalid procurement transition.")

        self.procurement_status = "Ordered"

        record = self._procurement(status="Ordered")

        record["supplier_order_id"] = supplier_order_id

        if actual_supplier_cost is None:
            record["actual_supplier_cost"] = None

        else:
            record["actual_supplier_cost"] = float(actual_supplier_cost)

        record["ordered_by"] = ordered_by or "Manager"

        if supplier_order_date:
            record["supplier_order_date"] = supplier_order_date

        return record

    def receive(
        self,
        procurement_id: str,
        *,
        received_by: str = "",
    ) -> dict[str, Any]:
        if procurement_id == "MISSING":
            raise ProcurementNotFoundError("Procurement request not found.")

        if procurement_id == "LOCKED":
            raise ProcurementStateError(
                ("Only an Ordered procurement " "can be marked Received.")
            )

        self.procurement_status = "Received"

        record = self._procurement(status="Received")

        record["received_by"] = received_by or "Receiver"

        return record

    def cancel(
        self,
        procurement_id: str,
        *,
        cancelled_by: str = "",
        reason: str = "",
    ) -> dict[str, Any]:
        if procurement_id == "MISSING":
            raise ProcurementNotFoundError("Procurement request not found.")

        if procurement_id == "LOCKED":
            raise ProcurementStateError("Invalid procurement transition.")

        self.procurement_status = "Cancelled"

        record = self._procurement(status="Cancelled")

        record["cancelled_by"] = cancelled_by or "Manager"

        record["cancellation_reason"] = reason or "Repair cancelled"

        return record


@pytest.fixture()
def fake_service() -> FakeProcurementService:
    return FakeProcurementService()


@pytest.fixture()
def client(
    fake_service: FakeProcurementService,
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[api_app_module.get_procurement_service] = (
        lambda: fake_service
    )

    try:
        yield TestClient(app)

    finally:
        app.dependency_overrides.pop(
            api_app_module.get_procurement_service,
            None,
        )


def test_create_procurement(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/repairs/RPR000001/procurements",
        json={
            "supplier": "Mobile Sentrix",
            "requested_by": "Test User",
            "notes": "Need replacement part",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["procurement_id"] == "PROC000001"

    assert payload["repair_id"] == "RPR000001"

    assert payload["procurement_status"] == "Pending Approval"


def test_create_procurement_missing_repair(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/repairs/MISSING/procurements",
        json={},
    )

    assert response.status_code == 404

    assert response.json() == {"detail": "Repair ticket not found."}


def test_list_repair_procurements(
    client: TestClient,
) -> None:
    response = client.get("/api/repairs/RPR000001/procurements")

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1

    assert payload[0]["procurement_id"] == "PROC000001"


def test_list_repair_procurements_missing_repair(
    client: TestClient,
) -> None:
    response = client.get("/api/repairs/MISSING/procurements")

    assert response.status_code == 404

    assert response.json() == {"detail": "Repair ticket not found."}


def test_get_procurement(
    client: TestClient,
) -> None:
    response = client.get("/api/procurements/PROC000001")

    assert response.status_code == 200

    assert response.json()["procurement_id"] == "PROC000001"


def test_get_procurement_missing(
    client: TestClient,
) -> None:
    response = client.get("/api/procurements/MISSING")

    assert response.status_code == 404

    assert response.json() == {"detail": ("Procurement request not found.")}


def test_add_procurement_item(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/PROC000001/items",
        json={
            "supplier": "Mobile Sentrix",
            "supplier_product_id": "249690",
            "supplier_sku": "107182127725",
            "product_name": "iHeater Pro",
            "quantity": 2,
            "unit_cost": 351.04,
            "supplier_in_stock": True,
            "supplier_stock_quantity": 3,
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["procurement_item_id"] == "PRI000001"

    assert payload["supplier_product_id"] == "249690"

    assert payload["supplier_sku"] == "107182127725"

    assert payload["quantity"] == 2

    assert payload["unit_cost"] == pytest.approx(351.04)

    assert payload["estimated_line_total"] == pytest.approx(702.08)

    assert payload["supplier_in_stock"] is True

    assert payload["supplier_stock_quantity"] == 3


def test_add_item_validation_error(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/PROC000001/items",
        json={
            "quantity": 1,
        },
    )

    assert response.status_code == 422


def test_add_item_missing_procurement(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/MISSING/items",
        json={
            "supplier_sku": "SKU001",
            "quantity": 1,
        },
    )

    assert response.status_code == 404


def test_add_item_state_conflict(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/LOCKED/items",
        json={
            "supplier_sku": "SKU001",
            "quantity": 1,
        },
    )

    assert response.status_code == 409


def test_list_procurement_items(
    client: TestClient,
) -> None:
    response = client.get("/api/procurements/PROC000001/items")

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1

    assert payload[0]["supplier_sku"] == "107182127725"

    assert payload[0]["supplier_in_stock"] is True


def test_list_procurement_items_missing(
    client: TestClient,
) -> None:
    response = client.get("/api/procurements/MISSING/items")

    assert response.status_code == 404


def test_procurement_summary(
    client: TestClient,
) -> None:
    response = client.get("/api/procurements/PROC000001/summary")

    assert response.status_code == 200

    payload = response.json()

    assert payload["item_count"] == 1

    assert payload["requested_units"] == 1

    assert payload["received_units"] == 0

    assert payload["estimated_total"] == pytest.approx(351.04)


def test_procurement_summary_missing(
    client: TestClient,
) -> None:
    response = client.get("/api/procurements/MISSING/summary")

    assert response.status_code == 404


def test_approve_procurement(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/PROC000001/approve",
        json={
            "actor": "Manager",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["procurement_status"] == "Approved"

    assert payload["approved_by"] == "Manager"


def test_approve_empty_procurement(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/EMPTY/approve",
        json={
            "actor": "Manager",
        },
    )

    assert response.status_code == 422


def test_mark_ready_for_order(
    client: TestClient,
) -> None:
    response = client.post("/api/procurements/PROC000001/ready")

    assert response.status_code == 200

    assert response.json()["procurement_status"] == "Ready for Order"


def test_reject_procurement(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/PROC000001/reject",
        json={
            "actor": "Manager",
            "reason": "Not required",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["procurement_status"] == "Rejected"

    assert payload["rejected_by"] == "Manager"

    assert payload["rejection_reason"] == "Not required"


def test_record_manual_order(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/PROC000001/order",
        json={
            "supplier_order_id": ("MS-ORDER-1001"),
            "actual_supplier_cost": 351.04,
            "ordered_by": "Manager",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["procurement_status"] == "Ordered"

    assert payload["supplier_order_id"] == "MS-ORDER-1001"

    assert payload["actual_supplier_cost"] == pytest.approx(351.04)


def test_receive_procurement(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/PROC000001/receive",
        json={
            "received_by": "Receiver",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["procurement_status"] == "Received"

    assert payload["received_by"] == "Receiver"


def test_cancel_procurement(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/procurements/PROC000001/cancel",
        json={
            "actor": "Manager",
            "reason": "Repair cancelled",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["procurement_status"] == "Cancelled"

    assert payload["cancelled_by"] == "Manager"

    assert payload["cancellation_reason"] == "Repair cancelled"


@pytest.mark.parametrize(
    (
        "path",
        "payload",
    ),
    [
        (
            "/api/procurements/LOCKED/approve",
            {
                "actor": "Manager",
            },
        ),
        (
            "/api/procurements/LOCKED/reject",
            {
                "actor": "Manager",
                "reason": "No",
            },
        ),
        (
            "/api/procurements/LOCKED/order",
            {
                "supplier_order_id": "MS-1",
            },
        ),
        (
            "/api/procurements/LOCKED/receive",
            {
                "received_by": "Receiver",
            },
        ),
        (
            "/api/procurements/LOCKED/cancel",
            {
                "actor": "Manager",
            },
        ),
    ],
)
def test_state_conflicts_return_409(
    client: TestClient,
    path: str,
    payload: dict[str, Any],
) -> None:
    response = client.post(
        path,
        json=payload,
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    (
        "path",
        "payload",
    ),
    [
        (
            "/api/procurements/MISSING/approve",
            {
                "actor": "Manager",
            },
        ),
        (
            "/api/procurements/MISSING/reject",
            {
                "actor": "Manager",
            },
        ),
        (
            "/api/procurements/MISSING/order",
            {
                "supplier_order_id": "MS-1",
            },
        ),
        (
            "/api/procurements/MISSING/receive",
            {
                "received_by": "Receiver",
            },
        ),
        (
            "/api/procurements/MISSING/cancel",
            {
                "actor": "Manager",
            },
        ),
    ],
)
def test_state_actions_missing_return_404(
    client: TestClient,
    path: str,
    payload: dict[str, Any],
) -> None:
    response = client.post(
        path,
        json=payload,
    )

    assert response.status_code == 404
