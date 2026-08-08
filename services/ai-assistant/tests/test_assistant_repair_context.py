from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings


def make_test_settings(
    tmp_path: Path,
) -> Settings:
    return Settings(
        database_url=(f"sqlite:///{tmp_path / 'assistant.db'}"),
        database_migration_mode=("auto-test-only"),
        auth_mode="development_header",
        allow_development_header_auth=True,
        coding_provider="mock",
        openai_enabled=False,
        external_providers_enabled=False,
        rate_limit_per_minute=500,
    )


def developer_headers(
    user_id: str = "local-developer",
) -> dict[str, str]:
    return {
        "X-Nocturnix-Dev-User": user_id,
    }


def create_repair_fixture(
    client: TestClient,
    *,
    user_id: str = "local-developer",
) -> dict[str, object]:
    headers = developer_headers(user_id)

    customer_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "first_name": "Avery",
            "last_name": "Stone",
            "email": "avery@example.com",
            "phone": "5551234567",
            "preferred_contact_method": ("phone"),
            "status": "active",
        },
    )

    assert customer_response.status_code == 201, customer_response.text

    customer = customer_response.json()

    device_response = client.post(
        "/api/v1/customer-devices",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "device_type": "laptop",
            "manufacturer": "Apple",
            "model": "MacBook Pro",
            "serial_number": "NX-TEST-001",
        },
    )

    assert device_response.status_code == 201, device_response.text

    device = device_response.json()

    ticket_response = client.post(
        "/api/v1/repair-tickets",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "customer_device_id": (device["id"]),
            "priority": "high",
            "issue_description": ("Device does not power on."),
            "diagnostic_summary": ("Initial intake inspection."),
            "estimated_cost_cents": 25000,
            "currency": "USD",
            "intake_channel": "walk_in",
        },
    )

    assert ticket_response.status_code == 201, ticket_response.text

    ticket = ticket_response.json()

    note_response = client.post(
        (f"/api/v1/repair-tickets/{ticket['id']}/notes"),
        headers=headers,
        json={
            "note_type": "diagnostic",
            "body": ("No measurable power draw during initial test."),
            "customer_visible": False,
        },
    )

    assert note_response.status_code == 201, note_response.text

    line_item_response = client.post(
        (f"/api/v1/repair-tickets/{ticket['id']}/line-items"),
        headers=headers,
        json={
            "line_type": "labor",
            "description": ("Diagnostic labor"),
            "quantity": 1,
            "unit_price_cents": 7500,
            "discount_cents": 0,
            "taxable": True,
            "currency": "USD",
        },
    )

    assert line_item_response.status_code == 201, line_item_response.text

    return {
        "customer": customer,
        "device": device,
        "ticket": ticket,
        "note": note_response.json(),
        "line_item": (line_item_response.json()),
    }


def test_assistant_can_read_repair_ticket_context(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        fixture = create_repair_fixture(client)

        ticket = fixture["ticket"]

        assert isinstance(
            ticket,
            dict,
        )

        response = client.get(
            (f"/api/assistant/repair/tickets/{ticket['id']}"),
            headers=developer_headers(),
        )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["ticket"]["id"] == (ticket["id"])

    assert body["ticket"]["ticket_number"] == ticket["ticket_number"]

    assert body["customer"]["first_name"] == ("Avery")

    assert body["customer"]["last_name"] == ("Stone")

    assert body["device"]["manufacturer"] == ("Apple")

    assert body["device"]["model"] == ("MacBook Pro")

    assert len(body["notes"]) == 1

    assert body["notes"][0]["body"] == ("No measurable power draw during initial test.")

    assert len(body["status_history"]) == 1

    assert body["status_history"][0]["to_status"] == "received"

    assert len(body["line_items"]) == 1

    assert body["line_items"][0]["description"] == "Diagnostic labor"

    assert body["financial_summary"]["line_item_count"] == 1

    assert body["financial_summary"]["gross_subtotal_cents"] == 7500

    assert body["financial_summary"]["net_subtotal_cents"] == 7500


def test_assistant_lists_open_repair_tickets(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        fixture = create_repair_fixture(client)

        ticket = fixture["ticket"]

        assert isinstance(
            ticket,
            dict,
        )

        response = client.get(
            "/api/assistant/repair/tickets",
            headers=developer_headers(),
        )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["total"] == 1

    assert len(body["items"]) == 1

    item = body["items"][0]

    assert item["id"] == ticket["id"]

    assert item["status"] == "received"

    assert item["priority"] == "high"

    assert item["customer_name"] == ("Avery Stone")

    assert item["device_label"] == ("Apple MacBook Pro")


def test_assistant_filters_repair_tickets_by_status(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        create_repair_fixture(client)

        matching = client.get(
            ("/api/assistant/repair/tickets?status=received"),
            headers=developer_headers(),
        )

        completed = client.get(
            ("/api/assistant/repair/tickets?status=completed"),
            headers=developer_headers(),
        )

    assert matching.status_code == 200
    assert matching.json()["total"] == 1

    assert completed.status_code == 200
    assert completed.json()["total"] == 0


def test_other_owner_cannot_read_assistant_repair_context(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        fixture = create_repair_fixture(
            client,
            user_id="repair-owner",
        )

        ticket = fixture["ticket"]

        assert isinstance(
            ticket,
            dict,
        )

        response = client.get(
            (f"/api/assistant/repair/tickets/{ticket['id']}"),
            headers=developer_headers("different-owner"),
        )

    assert response.status_code == 404

    assert response.json()["detail"] == ("Repair ticket not found.")


def test_missing_repair_ticket_returns_404(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        response = client.get(
            ("/api/assistant/repair/tickets/missing-ticket"),
            headers=developer_headers(),
        )

    assert response.status_code == 404

    assert response.json()["detail"] == ("Repair ticket not found.")


def test_assistant_repair_context_requires_authentication(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        response = client.get("/api/assistant/repair/tickets")

    assert response.status_code == 401


def test_assistant_repair_context_has_no_write_route(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        fixture = create_repair_fixture(client)

        ticket = fixture["ticket"]

        assert isinstance(
            ticket,
            dict,
        )

        response = client.post(
            (f"/api/assistant/repair/tickets/{ticket['id']}"),
            headers=developer_headers(),
            json={
                "status": "completed",
            },
        )

    assert response.status_code == 405
