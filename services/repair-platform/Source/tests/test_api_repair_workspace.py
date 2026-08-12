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
            "customer_id": "CUS000100",
            "device_id": "DEV000100",
            "repair_status": "In Repair",
            "problem_description": "Broken screen",
            "notes": "Technician notes",
            "estimated_cost": 149.99,
            "final_cost": None,
            "intake_date": "2026-08-12T10:00:00",
            "technician": "Ryan Brown",
            "priority": "Urgent",
            "due_date": "2026-08-15",
            "diagnosis": "Display assembly failed",
            "date_completed": "",
            "date_picked_up": "",
            "warranty": True,
            "last_modified": "2026-08-12T11:00:00",
        }

    def get_customer(
        self,
        customer_id: str,
    ) -> dict[str, Any] | None:
        if customer_id != "CUS000100":
            return None

        return {
            "customer_id": "CUS000100",
            "customer_type": "Individual",
            "first_name": "Alex",
            "last_name": "Customer",
            "business_name": "",
            "email": "alex@example.com",
            "mobile_phone": "555-0100",
            "preferred_contact": "Text",
        }

    def get_customer_device(
        self,
        device_id: str,
    ) -> dict[str, Any] | None:
        if device_id != "DEV000100":
            return None

        return {
            "device_id": "DEV000100",
            "customer_id": "CUS000100",
            "catalog_device_id": "CAT000100",
            "manufacturer": "Apple",
            "device_family": "iPhone",
            "device_model": "iPhone 15",
            "serial_number": "SERIAL100",
            "imei_service_tag": "IMEI100",
            "color": "Black",
            "storage": "128GB",
            "carrier": "Unlocked",
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


def test_repair_workspace_returns_joined_data(
    client: TestClient,
) -> None:
    response = client.get("/api/repairs/RPR000100/workspace")

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == "RPR000100"
    assert payload["customer_id"] == "CUS000100"
    assert payload["device_id"] == "DEV000100"

    assert payload["repair_status"] == "In Repair"
    assert payload["problem_description"] == "Broken screen"
    assert payload["diagnosis"] == "Display assembly failed"
    assert payload["estimated_cost"] == 149.99
    assert payload["final_cost"] is None
    assert payload["priority"] == "Urgent"
    assert payload["warranty"] is True

    assert payload["customer_type"] == "Individual"
    assert payload["first_name"] == "Alex"
    assert payload["last_name"] == "Customer"
    assert payload["email"] == "alex@example.com"
    assert payload["mobile_phone"] == "555-0100"
    assert payload["preferred_contact"] == "Text"

    assert payload["catalog_device_id"] == "CAT000100"
    assert payload["manufacturer"] == "Apple"
    assert payload["device_family"] == "iPhone"
    assert payload["device_model"] == "iPhone 15"
    assert payload["serial_number"] == "SERIAL100"
    assert payload["imei_service_tag"] == "IMEI100"
    assert payload["color"] == "Black"
    assert payload["storage"] == "128GB"
    assert payload["carrier"] == "Unlocked"


def test_repair_workspace_returns_404_when_repair_missing(
    client: TestClient,
) -> None:
    response = client.get("/api/repairs/MISSING/workspace")

    assert response.status_code == 404

    assert response.json() == {"detail": "Repair ticket not found."}
