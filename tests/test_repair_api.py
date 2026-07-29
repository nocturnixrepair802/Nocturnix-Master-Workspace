from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings
from nocturnix.repair_models import RepairTaxPolicyCreateRequest

OWNER_HEADERS = {"X-Nocturnix-Dev-User": "repair-owner-001"}
OTHER_HEADERS = {"X-Nocturnix-Dev-User": "repair-owner-002"}


@pytest.fixture
def repair_client(tmp_path: Path):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path / 'repair_api.db'}",
            database_migration_mode="auto-test-only",
            auth_mode="development_header",
            allow_development_header_auth=True,
            rate_limit_per_minute=500,
        )
    )
    with TestClient(app) as client:
        yield client
    cast(Any, app).state.container.engine.dispose()


def create_customer(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/v1/customers",
        headers=OWNER_HEADERS,
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.test",
            "phone": "802-555-0100",
            "preferred_contact_method": "email",
            "notes": "Primary repair contact",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_device(client: TestClient, customer_id: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/customer-devices",
        headers=OWNER_HEADERS,
        json={
            "customer_id": customer_id,
            "device_type": "laptop",
            "manufacturer": "Framework",
            "model": "Laptop 13",
            "serial_number": "FW-TEST-001",
            "color": "black",
            "storage_capacity": "1 TB",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_ticket(client: TestClient, customer_id: str, device_id: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/repair-tickets",
        headers=OWNER_HEADERS,
        json={
            "customer_id": customer_id,
            "customer_device_id": device_id,
            "priority": "high",
            "issue_description": "Display intermittently turns off",
            "estimated_cost_cents": 25000,
            "approved_cost_cents": 20000,
            "currency": "usd",
            "intake_channel": "walk_in",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_line_item(
    client: TestClient,
    ticket_id: str,
    *,
    line_type: str = "labor",
    description: str = "Diagnostic labor",
    quantity: int = 1,
    unit_price_cents: int = 10000,
    discount_cents: int = 0,
    taxable: bool = True,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/repair-tickets/{ticket_id}/line-items",
        headers=OWNER_HEADERS,
        json={
            "line_type": line_type,
            "description": description,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents,
            "discount_cents": discount_cents,
            "taxable": taxable,
            "currency": "USD",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def get_financial_summary(
    client: TestClient,
    ticket_id: str,
) -> dict[str, Any]:
    response = client.get(
        f"/api/v1/repair-tickets/{ticket_id}/financial-summary",
        headers=OWNER_HEADERS,
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_repair_management_end_to_end(repair_client: TestClient) -> None:
    customer = create_customer(repair_client)
    assert customer["owner_user_id"] == "repair-owner-001"
    assert customer["email"] == "ada@example.test"

    customers = repair_client.get(
        "/api/v1/customers?search=lovelace&limit=10", headers=OWNER_HEADERS
    )
    assert customers.status_code == 200
    assert customers.json()["total"] == 1
    assert customers.json()["items"][0]["id"] == customer["id"]

    updated_customer = repair_client.put(
        f"/api/v1/customers/{customer['id']}",
        headers=OWNER_HEADERS,
        json={"company_name": "Analytical Engines LLC"},
    )
    assert updated_customer.status_code == 200
    assert updated_customer.json()["company_name"] == "Analytical Engines LLC"

    device = create_device(repair_client, customer["id"])
    devices = repair_client.get(
        f"/api/v1/customers/{customer['id']}/devices", headers=OWNER_HEADERS
    )
    assert devices.status_code == 200
    assert devices.json()["total"] == 1
    assert devices.json()["items"][0]["id"] == device["id"]

    ticket = create_ticket(repair_client, customer["id"], device["id"])
    assert ticket["status"] == "received"
    assert ticket["priority"] == "high"
    assert ticket["currency"] == "USD"
    assert ticket["ticket_number"]

    tickets = repair_client.get(
        "/api/v1/repair-tickets?status=received&search=display",
        headers=OWNER_HEADERS,
    )
    assert tickets.status_code == 200
    assert tickets.json()["total"] == 1
    assert tickets.json()["items"][0]["id"] == ticket["id"]

    status_change = repair_client.post(
        f"/api/v1/repair-tickets/{ticket['id']}/status",
        headers=OWNER_HEADERS,
        json={"status": "diagnosing", "reason": "Bench inspection started"},
    )
    assert status_change.status_code == 200
    assert status_change.json()["status"] == "diagnosing"

    history = repair_client.get(
        f"/api/v1/repair-tickets/{ticket['id']}/status-history",
        headers=OWNER_HEADERS,
    )
    assert history.status_code == 200
    assert history.json()[-1]["to_status"] == "diagnosing"
    assert history.json()[-1]["changed_by_user_id"] == "repair-owner-001"

    note = repair_client.post(
        f"/api/v1/repair-tickets/{ticket['id']}/notes",
        headers=OWNER_HEADERS,
        json={
            "note_type": "customer_update",
            "body": "Diagnostics are in progress.",
            "customer_visible": True,
        },
    )
    assert note.status_code == 201
    note_id = note.json()["id"]

    visible_notes = repair_client.get(
        f"/api/v1/repair-tickets/{ticket['id']}/notes?customer_visible_only=true",
        headers=OWNER_HEADERS,
    )
    assert visible_notes.status_code == 200
    assert [item["id"] for item in visible_notes.json()] == [note_id]

    updated_note = repair_client.put(
        f"/api/v1/repair-ticket-notes/{note_id}",
        headers=OWNER_HEADERS,
        json={"body": "Diagnostics completed; estimate is ready."},
    )
    assert updated_note.status_code == 200
    assert updated_note.json()["body"].startswith("Diagnostics completed")


def test_ticket_financial_summary(repair_client: TestClient) -> None:
    customer = create_customer(repair_client)
    device = create_device(repair_client, customer["id"])
    ticket = create_ticket(repair_client, customer["id"], device["id"])

    empty = get_financial_summary(repair_client, ticket["id"])

    assert empty["line_item_count"] == 0
    assert empty["gross_subtotal_cents"] == 0
    assert empty["discount_total_cents"] == 0
    assert empty["net_subtotal_cents"] == 0
    assert empty["taxable_subtotal_cents"] == 0
    assert empty["non_taxable_subtotal_cents"] == 0

    create_line_item(
        repair_client,
        ticket["id"],
        line_type="labor",
        quantity=2,
        unit_price_cents=10000,
        discount_cents=2000,
        taxable=True,
    )

    create_line_item(
        repair_client,
        ticket["id"],
        line_type="part",
        quantity=1,
        unit_price_cents=5000,
        taxable=False,
    )

    summary = get_financial_summary(repair_client, ticket["id"])

    assert summary["currency"] == "USD"
    assert summary["line_item_count"] == 2
    assert summary["gross_subtotal_cents"] == 25000
    assert summary["discount_total_cents"] == 2000
    assert summary["net_subtotal_cents"] == 23000
    assert summary["taxable_subtotal_cents"] == 18000
    assert summary["non_taxable_subtotal_cents"] == 5000


def test_repair_ownership_authentication_and_errors(repair_client: TestClient) -> None:
    assert repair_client.get("/api/v1/customers").status_code == 401

    customer = create_customer(repair_client)
    device = create_device(repair_client, customer["id"])
    ticket = create_ticket(repair_client, customer["id"], device["id"])

    hidden_customer = repair_client.get(
        f"/api/v1/customers/{customer['id']}", headers=OTHER_HEADERS
    )
    assert hidden_customer.status_code == 404
    assert hidden_customer.json()["error"]["code"] == "repair_not_found"

    invalid_transition = repair_client.post(
        f"/api/v1/repair-tickets/{ticket['id']}/status",
        headers=OWNER_HEADERS,
        json={"status": "completed"},
    )
    assert invalid_transition.status_code == 409
    assert invalid_transition.json()["error"]["code"] == "invalid_repair_status_transition"

    duplicate_status = repair_client.post(
        f"/api/v1/repair-tickets/{ticket['id']}/status",
        headers=OWNER_HEADERS,
        json={"status": "received"},
    )
    assert duplicate_status.status_code == 409
    assert duplicate_status.json()["error"]["code"] == "repair_conflict"

    invalid_note = repair_client.post(
        f"/api/v1/repair-tickets/{ticket['id']}/notes",
        headers=OWNER_HEADERS,
        json={
            "note_type": "internal",
            "body": "Internal-only details",
            "customer_visible": True,
        },
    )
    assert invalid_note.status_code == 422

    invalid_cost = repair_client.put(
        f"/api/v1/repair-tickets/{ticket['id']}",
        headers=OWNER_HEADERS,
        json={"estimated_cost_cents": 10000, "approved_cost_cents": 15000},
    )
    assert invalid_cost.status_code == 422


def test_repair_pagination_and_device_customer_validation(repair_client: TestClient) -> None:
    first = create_customer(repair_client)
    second_response = repair_client.post(
        "/api/v1/customers",
        headers=OWNER_HEADERS,
        json={
            "first_name": "Grace",
            "last_name": "Hopper",
            "phone": "802-555-0101",
            "preferred_contact_method": "phone",
        },
    )
    assert second_response.status_code == 201
    second = second_response.json()

    page = repair_client.get("/api/v1/customers?offset=1&limit=1", headers=OWNER_HEADERS)
    assert page.status_code == 200
    assert page.json()["total"] == 2
    assert page.json()["offset"] == 1
    assert page.json()["limit"] == 1
    assert len(page.json()["items"]) == 1

    first_device = create_device(repair_client, first["id"])
    mismatch = repair_client.post(
        "/api/v1/repair-tickets",
        headers=OWNER_HEADERS,
        json={
            "customer_id": second["id"],
            "customer_device_id": first_device["id"],
            "issue_description": "Customer and device mismatch",
        },
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["error"]["code"] == "repair_conflict"


def test_repair_tax_policy_create_request_trims_name() -> None:
    request = RepairTaxPolicyCreateRequest(
        name="  Standard Sales Tax  ",
        tax_rate_basis_points=725,
        is_default=True,
        effective_at=datetime.now(UTC),
    )

    assert request.name == "Standard Sales Tax"
