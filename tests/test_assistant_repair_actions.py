from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings


def make_test_settings(
    tmp_path: Path,
) -> Settings:
    return Settings(
        database_url=(f"sqlite:///{tmp_path / 'assistant.db'}"),
        database_migration_mode="auto-test-only",
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


def create_ticket(
    client: TestClient,
    *,
    user_id: str = "local-developer",
) -> dict[str, Any]:
    headers = developer_headers(user_id)

    customer_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "first_name": "Morgan",
            "last_name": "Reed",
            "email": "morgan@example.com",
            "phone": "5555551212",
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
            "manufacturer": "Dell",
            "model": "XPS 15",
            "serial_number": "NX-ACTION-001",
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
            "priority": "normal",
            "issue_description": ("System intermittently shuts down."),
            "currency": "USD",
            "intake_channel": "walk_in",
        },
    )

    assert ticket_response.status_code == 201, ticket_response.text

    return ticket_response.json()


def propose_note(
    client: TestClient,
    ticket_id: str,
    *,
    user_id: str = "local-developer",
    body: str = ("Assistant proposed diagnostic note."),
):
    return client.post(
        ("/api/assistant/repair/actions/notes/propose"),
        headers=developer_headers(user_id),
        json={
            "ticket_id": ticket_id,
            "note_type": "diagnostic",
            "body": body,
            "customer_visible": False,
        },
    )


def apply_proposal(
    client: TestClient,
    proposal_id: str,
    *,
    user_id: str = "local-developer",
    confirm: bool = True,
):
    return client.post(
        (f"/api/assistant/repair/actions/{proposal_id}/apply"),
        headers=developer_headers(user_id),
        json={
            "confirm": confirm,
        },
    )


def list_ticket_notes(
    client: TestClient,
    ticket_id: str,
    *,
    user_id: str = "local-developer",
):
    return client.get(
        (f"/api/v1/repair-tickets/{ticket_id}/notes"),
        headers=developer_headers(user_id),
    )


def test_repair_note_proposal_does_not_write_note(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        ticket = create_ticket(client)

        response = propose_note(
            client,
            ticket["id"],
        )

        notes_response = list_ticket_notes(
            client,
            ticket["id"],
        )

    assert response.status_code == 200, response.text

    proposal = response.json()

    assert proposal["action_type"] == ("add_ticket_note")

    assert proposal["status"] == "pending"

    assert proposal["ticket_id"] == (ticket["id"])

    assert proposal["note_type"] == ("diagnostic")

    assert proposal["body"] == ("Assistant proposed diagnostic note.")

    assert proposal["applied_at"] is None

    assert proposal["applied_by_user_id"] is None

    assert notes_response.status_code == 200
    assert notes_response.json() == []


def test_repair_action_proposal_persists_across_requests(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        ticket = create_ticket(client)

        create_response = propose_note(
            client,
            ticket["id"],
        )

        assert create_response.status_code == 200, create_response.text

        proposal = create_response.json()

        get_response = client.get(
            (f"/api/assistant/repair/actions/{proposal['proposal_id']}"),
            headers=developer_headers(),
        )

    assert get_response.status_code == 200

    retrieved = get_response.json()

    assert retrieved["proposal_id"] == proposal["proposal_id"]

    assert retrieved["status"] == "pending"

    assert retrieved["body"] == ("Assistant proposed diagnostic note.")


def test_repair_action_requires_explicit_confirmation(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        ticket = create_ticket(client)

        proposal_response = propose_note(
            client,
            ticket["id"],
        )

        proposal = proposal_response.json()

        response = apply_proposal(
            client,
            proposal["proposal_id"],
            confirm=False,
        )

        notes_response = list_ticket_notes(
            client,
            ticket["id"],
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Repair action application requires explicit confirmation."
    )

    assert notes_response.json() == []


def test_confirmed_repair_action_creates_note(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        ticket = create_ticket(client)

        proposal_response = propose_note(
            client,
            ticket["id"],
            body=("Battery connector reseated during diagnostic."),
        )

        assert proposal_response.status_code == 200, proposal_response.text

        proposal = proposal_response.json()

        apply_response = apply_proposal(
            client,
            proposal["proposal_id"],
        )

        notes_response = list_ticket_notes(
            client,
            ticket["id"],
        )

    assert apply_response.status_code == 200, apply_response.text

    applied = apply_response.json()

    assert applied["status"] == "applied"

    assert applied["action_type"] == ("add_ticket_note")

    assert applied["ticket_id"] == (ticket["id"])

    assert applied["created_note_id"]

    assert applied["applied_at"]

    assert applied["applied_by_user_id"] == "local-developer"

    assert notes_response.status_code == 200

    notes = notes_response.json()

    assert len(notes) == 1

    assert notes[0]["id"] == (applied["created_note_id"])

    assert notes[0]["body"] == ("Battery connector reseated during diagnostic.")

    assert notes[0]["note_type"] == ("diagnostic")


def test_applied_repair_action_is_persisted_as_applied(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        ticket = create_ticket(client)

        proposal = propose_note(
            client,
            ticket["id"],
        ).json()

        apply_response = apply_proposal(
            client,
            proposal["proposal_id"],
        )

        assert apply_response.status_code == 200, apply_response.text

        history_response = client.get(
            (f"/api/assistant/repair/actions/{proposal['proposal_id']}"),
            headers=developer_headers(),
        )

    assert history_response.status_code == 200

    body = history_response.json()

    assert body["status"] == "applied"
    assert body["applied_at"]
    assert body["applied_by_user_id"] == "local-developer"
    assert body["failure_reason"] is None


def test_repair_action_rejects_second_application(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        ticket = create_ticket(client)

        proposal = propose_note(
            client,
            ticket["id"],
        ).json()

        first_response = apply_proposal(
            client,
            proposal["proposal_id"],
        )

        second_response = apply_proposal(
            client,
            proposal["proposal_id"],
        )

        notes_response = list_ticket_notes(
            client,
            ticket["id"],
        )

    assert first_response.status_code == 200

    assert second_response.status_code == 409

    assert len(notes_response.json()) == 1


def test_other_owner_cannot_read_repair_action_proposal(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        ticket = create_ticket(
            client,
            user_id="repair-owner",
        )

        proposal_response = propose_note(
            client,
            ticket["id"],
            user_id="repair-owner",
        )

        assert proposal_response.status_code == 200, proposal_response.text

        proposal = proposal_response.json()

        response = client.get(
            (f"/api/assistant/repair/actions/{proposal['proposal_id']}"),
            headers=developer_headers("different-owner"),
        )

    assert response.status_code == 404

    assert response.json()["detail"] == ("Repair action proposal not found.")


def test_other_owner_cannot_apply_repair_action(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        ticket = create_ticket(
            client,
            user_id="repair-owner",
        )

        proposal = propose_note(
            client,
            ticket["id"],
            user_id="repair-owner",
        ).json()

        response = apply_proposal(
            client,
            proposal["proposal_id"],
            user_id="different-owner",
        )

        notes_response = list_ticket_notes(
            client,
            ticket["id"],
            user_id="repair-owner",
        )

    assert response.status_code == 404

    assert notes_response.json() == []


def test_missing_repair_action_proposal_returns_404(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        get_response = client.get(
            ("/api/assistant/repair/actions/missing-proposal"),
            headers=developer_headers(),
        )

        apply_response = apply_proposal(
            client,
            "missing-proposal",
        )

    assert get_response.status_code == 404
    assert apply_response.status_code == 404


def test_repair_action_requires_authentication(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        get_response = client.get("/api/assistant/repair/actions/missing-proposal")

        propose_response = client.post(
            ("/api/assistant/repair/actions/notes/propose"),
            json={
                "ticket_id": "ticket-missing",
                "note_type": "diagnostic",
                "body": "Test",
                "customer_visible": False,
            },
        )

        apply_response = client.post(
            ("/api/assistant/repair/actions/missing-proposal/apply"),
            json={
                "confirm": True,
            },
        )

    assert get_response.status_code == 401

    assert propose_response.status_code == 401

    assert apply_response.status_code == 401
