from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings

OWNER_HEADERS = {"X-Nocturnix-Dev-User": "dashboard-owner-001"}
OTHER_HEADERS = {"X-Nocturnix-Dev-User": "dashboard-owner-002"}


@pytest.fixture
def client(tmp_path: Path):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path / 'repair_dashboard.db'}",
            database_migration_mode="auto-test-only",
            auth_mode="development_header",
            allow_development_header_auth=True,
            rate_limit_per_minute=500,
        )
    )
    with TestClient(app) as test_client:
        yield test_client
    cast(Any, app).state.container.engine.dispose()


def create_customer(test_client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = test_client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "first_name": "Nina",
            "last_name": "Bench",
            "email": "nina@example.test",
            "phone": "802-555-0199",
            "preferred_contact_method": "email",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_device(
    test_client: TestClient, customer_id: str, headers: dict[str, str]
) -> dict[str, Any]:
    response = test_client.post(
        "/api/v1/customer-devices",
        headers=headers,
        json={
            "customer_id": customer_id,
            "device_type": "phone",
            "manufacturer": "Fairphone",
            "model": "5",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_ticket(
    test_client: TestClient,
    customer_id: str,
    device_id: str,
    headers: dict[str, str],
    *,
    priority: str = "urgent",
) -> dict[str, Any]:
    response = test_client.post(
        "/api/v1/repair-tickets",
        headers=headers,
        json={
            "customer_id": customer_id,
            "customer_device_id": device_id,
            "priority": priority,
            "issue_description": "USB-C port is loose",
            "estimated_cost_cents": 14900,
            "approved_cost_cents": 14900,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_repair_dashboard_aggregates_owner_repair_queue(client: TestClient) -> None:
    owner_customer = create_customer(client, OWNER_HEADERS)
    owner_device = create_device(client, owner_customer["id"], OWNER_HEADERS)
    owner_ticket = create_ticket(client, owner_customer["id"], owner_device["id"], OWNER_HEADERS)
    status_response = client.post(
        f"/api/v1/repair-tickets/{owner_ticket['id']}/status",
        headers=OWNER_HEADERS,
        json={"status": "diagnosing", "reason": "Bench triage started"},
    )
    assert status_response.status_code == 200, status_response.text

    other_customer = create_customer(client, OTHER_HEADERS)
    other_device = create_device(client, other_customer["id"], OTHER_HEADERS)
    create_ticket(client, other_customer["id"], other_device["id"], OTHER_HEADERS, priority="low")

    response = client.get("/api/v1/dashboard/repairs", headers=OWNER_HEADERS)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["development_only"] is True
    assert payload["summary"] == {
        "total_customers": 1,
        "total_devices": 1,
        "total_tickets": 1,
        "open_tickets": 1,
        "urgent_tickets": 1,
        "awaiting_approval": 0,
        "ready_for_pickup": 0,
        "completed_tickets": 0,
    }
    assert payload["tickets_by_status"]["diagnosing"] == 1
    assert payload["tickets_by_priority"]["urgent"] == 1
    assert payload["tickets_by_priority"]["low"] == 0
    assert payload["recent_queue"][0]["id"] == owner_ticket["id"]
    assert payload["recent_queue"][0]["customer_name"] == "Nina Bench"
    assert payload["recent_queue"][0]["device_label"] == "Fairphone 5"


def test_repair_dashboard_requires_auth_and_serves_static_page(client: TestClient) -> None:
    assert client.get("/api/v1/dashboard/repairs").status_code == 401

    page = client.get("/static/repairs-dashboard.html")

    assert page.status_code == 200
    assert "Repair Dashboard" in page.text
    assert "/api/v1/dashboard/repairs" in page.text
