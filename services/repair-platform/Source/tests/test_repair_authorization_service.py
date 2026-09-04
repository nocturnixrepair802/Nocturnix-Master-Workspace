from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from persistence.operations_db import OperationsDatabase
from services.repair_authorization_service import (
    RepairAuthorizationNotFoundError,
    RepairAuthorizationService,
    RepairAuthorizationStateError,
    RepairAuthorizationValidationError,
)
from tests.test_repair_authorization_persistence import (
    create_repair_pricing_item,
)


def test_create_repair_authorization(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    service = RepairAuthorizationService(database)

    authorization = service.create(
        "RPR000001",
        ["RPI000001"],
        terms_document_id="NMR-FRM-003",
        terms_version="1.0",
        now=datetime(
            2026,
            9,
            4,
            3,
            0,
            tzinfo=UTC,
        ),
    )

    assert authorization["authorization_id"] == "AUT000001"
    assert authorization["repair_id"] == "RPR000001"
    assert authorization["authorization_status"] == "PENDING"
    assert authorization["quoted_total_cents"] == 26999
    assert authorization["currency"] == "USD"
    assert authorization["terms_document_id"] == "NMR-FRM-003"
    assert authorization["terms_version"] == "1.0"

    items = database.list_repair_authorization_items("AUT000001")

    assert len(items) == 1
    assert items[0]["repair_pricing_item_id"] == "RPI000001"


def test_create_repair_authorization_requires_pricing_items(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    service = RepairAuthorizationService(database)

    with pytest.raises(
        RepairAuthorizationValidationError,
        match="At least one repair pricing item is required",
    ):
        service.create(
            "RPR000001",
            [],
        )


def test_create_repair_authorization_rejects_unknown_item(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    service = RepairAuthorizationService(database)

    with pytest.raises(
        RepairAuthorizationNotFoundError,
        match="Repair pricing item 'RPI999999' was not found",
    ):
        service.create(
            "RPR000001",
            ["RPI999999"],
        )


def test_create_repair_authorization_rejects_duplicate_items(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    service = RepairAuthorizationService(database)

    with pytest.raises(
        RepairAuthorizationValidationError,
        match="Duplicate repair pricing item IDs are not allowed",
    ):
        service.create(
            "RPR000001",
            [
                "RPI000001",
                "RPI000001",
            ],
        )


def test_authorize_pending_repair_authorization(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    service = RepairAuthorizationService(database)

    created = service.create(
        "RPR000001",
        ["RPI000001"],
        now=datetime(
            2026,
            9,
            4,
            3,
            0,
            tzinfo=UTC,
        ),
    )

    authorized = service.authorize(
        created["authorization_id"],
        customer_name="Test Customer",
        authorization_method="IN_PERSON",
        now=datetime(
            2026,
            9,
            4,
            3,
            5,
            tzinfo=UTC,
        ),
    )

    assert authorized["authorization_status"] == "AUTHORIZED"
    assert authorized["customer_name"] == "Test Customer"
    assert authorized["authorization_method"] == "IN_PERSON"
    assert authorized["authorized_at"] == "2026-09-04T03:05:00Z"
    assert authorized["declined_at"] is None

    events = database.list_repair_events("RPR000001")

    assert len(events) == 1
    assert events[0]["event_type"] == "authorization_authorized"
    assert events[0]["old_value"] == "PENDING"
    assert events[0]["new_value"] == "AUTHORIZED"
    assert events[0]["notes"] == "AUT000001"


def test_decline_pending_repair_authorization(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    service = RepairAuthorizationService(database)

    created = service.create(
        "RPR000001",
        ["RPI000001"],
        now=datetime(
            2026,
            9,
            4,
            3,
            0,
            tzinfo=UTC,
        ),
    )

    declined = service.decline(
        created["authorization_id"],
        now=datetime(
            2026,
            9,
            4,
            3,
            10,
            tzinfo=UTC,
        ),
    )

    assert declined["authorization_status"] == "DECLINED"
    assert declined["authorized_at"] is None
    assert declined["declined_at"] == "2026-09-04T03:10:00Z"

    events = database.list_repair_events("RPR000001")

    assert len(events) == 1
    assert events[0]["event_type"] == "authorization_declined"
    assert events[0]["old_value"] == "PENDING"
    assert events[0]["new_value"] == "DECLINED"
    assert events[0]["notes"] == "AUT000001"


def test_authorized_repair_authorization_cannot_be_declined(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    service = RepairAuthorizationService(database)

    created = service.create(
        "RPR000001",
        ["RPI000001"],
    )

    service.authorize(
        created["authorization_id"],
        customer_name="Test Customer",
        authorization_method="IN_PERSON",
    )

    with pytest.raises(
        RepairAuthorizationStateError,
        match="is not PENDING",
    ):
        service.decline(
            created["authorization_id"],
        )


def test_declined_repair_authorization_cannot_be_authorized(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    create_repair_pricing_item(database)

    service = RepairAuthorizationService(database)

    created = service.create(
        "RPR000001",
        ["RPI000001"],
    )

    service.decline(
        created["authorization_id"],
    )

    with pytest.raises(
        RepairAuthorizationStateError,
        match="is not PENDING",
    ):
        service.authorize(
            created["authorization_id"],
            customer_name="Test Customer",
            authorization_method="IN_PERSON",
        )
