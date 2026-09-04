from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import app as api_app_module
from api.app import app
from persistence.operations_db import OperationsDatabase
from services.repair_authorization_service import (
    RepairAuthorizationService,
)
from tests.test_repair_authorization_persistence import (
    create_repair_pricing_item,
)


@pytest.fixture
def repair_authorization_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, OperationsDatabase]]:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    monkeypatch.setattr(
        api_app_module,
        "get_database",
        lambda: database,
    )

    app.dependency_overrides[api_app_module.get_repair_authorization_service] = lambda: (
        RepairAuthorizationService(
            operations_database=database,
        )
    )

    client = TestClient(app)

    try:
        yield client, database

    finally:
        app.dependency_overrides.clear()


def test_create_repair_authorization(
    repair_authorization_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, database = repair_authorization_client

    response = client.post(
        "/api/repairs/RPR000001/authorizations",
        json={
            "repair_pricing_item_ids": [
                "RPI000001",
            ],
            "terms_document_id": "NMR-FRM-003",
            "terms_version": "1.0",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["authorization_id"] == "AUT000001"
    assert payload["repair_id"] == "RPR000001"
    assert payload["authorization_type"] == "REPAIR_QUOTE"
    assert payload["authorization_status"] == "PENDING"

    assert payload["quoted_total_cents"] == 26999
    assert payload["currency"] == "USD"

    assert payload["terms_document_id"] == "NMR-FRM-003"
    assert payload["terms_version"] == "1.0"

    assert payload["customer_name"] == ""
    assert payload["authorization_method"] == ""
    assert payload["authorized_at"] is None
    assert payload["declined_at"] is None

    assert payload["repair_pricing_item_ids"] == [
        "RPI000001",
    ]

    stored = database.get_repair_authorization("AUT000001")

    assert stored is not None
    assert stored["authorization_status"] == "PENDING"
    assert stored["quoted_total_cents"] == 26999


def test_list_repair_authorizations(
    repair_authorization_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_authorization_client

    created = client.post(
        "/api/repairs/RPR000001/authorizations",
        json={
            "repair_pricing_item_ids": [
                "RPI000001",
            ],
            "terms_document_id": "NMR-FRM-003",
            "terms_version": "1.0",
        },
    )

    assert created.status_code == 200

    response = client.get("/api/repairs/RPR000001/authorizations")

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1

    authorization = payload[0]

    assert authorization["authorization_id"] == "AUT000001"
    assert authorization["repair_id"] == "RPR000001"
    assert authorization["authorization_status"] == "PENDING"
    assert authorization["quoted_total_cents"] == 26999
    assert authorization["repair_pricing_item_ids"] == [
        "RPI000001",
    ]


def test_create_repair_authorization_unknown_repair(
    repair_authorization_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_authorization_client

    response = client.post(
        "/api/repairs/RPR999999/authorizations",
        json={
            "repair_pricing_item_ids": [
                "RPI000001",
            ],
        },
    )

    assert response.status_code == 404


def test_create_repair_authorization_requires_pricing_items(
    repair_authorization_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_authorization_client

    response = client.post(
        "/api/repairs/RPR000001/authorizations",
        json={
            "repair_pricing_item_ids": [],
        },
    )

    assert response.status_code == 422

    assert response.json()["detail"] == (
        "At least one repair pricing item is required."
    )


def test_list_repair_authorizations_unknown_repair(
    repair_authorization_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_authorization_client

    response = client.get("/api/repairs/RPR999999/authorizations")

    assert response.status_code == 404


def test_authorize_repair_authorization(
    repair_authorization_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, database = repair_authorization_client

    created = client.post(
        "/api/repairs/RPR000001/authorizations",
        json={
            "repair_pricing_item_ids": [
                "RPI000001",
            ],
        },
    )

    assert created.status_code == 200

    response = client.post(
        "/api/authorizations/AUT000001/authorize",
        json={
            "customer_name": "Test Customer",
            "authorization_method": "IN_PERSON",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["authorization_id"] == "AUT000001"
    assert payload["authorization_status"] == "AUTHORIZED"
    assert payload["customer_name"] == "Test Customer"
    assert payload["authorization_method"] == "IN_PERSON"
    assert payload["authorized_at"] is not None
    assert payload["declined_at"] is None
    assert payload["repair_pricing_item_ids"] == [
        "RPI000001",
    ]

    events = database.list_repair_events("RPR000001")

    assert len(events) == 1
    assert events[0]["event_type"] == "authorization_authorized"


def test_decline_repair_authorization(
    repair_authorization_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, database = repair_authorization_client

    created = client.post(
        "/api/repairs/RPR000001/authorizations",
        json={
            "repair_pricing_item_ids": [
                "RPI000001",
            ],
        },
    )

    assert created.status_code == 200

    response = client.post("/api/authorizations/AUT000001/decline")

    assert response.status_code == 200

    payload = response.json()

    assert payload["authorization_id"] == "AUT000001"
    assert payload["authorization_status"] == "DECLINED"
    assert payload["authorized_at"] is None
    assert payload["declined_at"] is not None

    events = database.list_repair_events("RPR000001")

    assert len(events) == 1
    assert events[0]["event_type"] == "authorization_declined"


def test_authorize_repair_authorization_rejects_invalid_state(
    repair_authorization_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_authorization_client

    created = client.post(
        "/api/repairs/RPR000001/authorizations",
        json={
            "repair_pricing_item_ids": [
                "RPI000001",
            ],
        },
    )

    assert created.status_code == 200

    first = client.post(
        "/api/authorizations/AUT000001/authorize",
        json={
            "customer_name": "Test Customer",
            "authorization_method": "IN_PERSON",
        },
    )

    assert first.status_code == 200

    second = client.post(
        "/api/authorizations/AUT000001/authorize",
        json={
            "customer_name": "Test Customer",
            "authorization_method": "IN_PERSON",
        },
    )

    assert second.status_code == 409


def test_authorize_unknown_authorization(
    repair_authorization_client: tuple[
        TestClient,
        OperationsDatabase,
    ],
) -> None:
    client, _ = repair_authorization_client

    response = client.post(
        "/api/authorizations/AUT999999/authorize",
        json={
            "customer_name": "Test Customer",
            "authorization_method": "IN_PERSON",
        },
    )

    assert response.status_code == 404
