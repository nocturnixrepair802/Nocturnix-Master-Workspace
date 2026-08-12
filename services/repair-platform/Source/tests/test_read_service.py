from __future__ import annotations

from typing import Any

import pytest

from desktop.services.api_client import (
    ApiRequestError,
)
from desktop.services.read_service import (
    ReadService,
    ReadServiceUnavailable,
)
from desktop.services.settings_service import (
    DesktopSettings,
)


class FakeLocalService:
    def __init__(self) -> None:
        self.dashboard_calls = 0
        self.operational_calls = 0
        self.repair_calls = 0

    def dashboard_counts(
        self,
    ) -> dict[str, int]:
        self.dashboard_calls += 1

        return {
            "customers": 1,
            "devices": 2,
            "repairs": 3,
            "open_repairs": 2,
        }

    def dashboard_operational_counts(
        self,
    ) -> dict[str, int]:
        self.operational_calls += 1

        return {
            "awaiting_diagnosis": 1,
            "awaiting_approval": 2,
            "in_repair": 3,
            "awaiting_parts": 4,
            "ready_for_pickup": 5,
            "urgent_repairs": 6,
        }

    def list_repairs(
        self,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        self.repair_calls += 1

        return [
            {
                "ticket_id": "LOCAL001",
                "repair_status": "In Repair",
            }
        ][:limit]


class FakeApiClient:
    def __init__(
        self,
        *,
        fail: bool = False,
    ) -> None:
        self.fail = fail

    def dashboard(
        self,
    ) -> dict[str, Any]:
        if self.fail:
            raise ApiRequestError("API unavailable")

        return {
            "customers": 10,
            "devices": 20,
            "repairs": 30,
            "repairs_by_status": {
                "Awaiting Diagnosis": 2,
                "Awaiting Approval": 3,
                "In Repair": 4,
                "Awaiting Parts": 5,
                "Ready for Pickup": 6,
                "Completed": 4,
                "Picked Up": 3,
                "Cancelled": 1,
            },
        }

    def repair_queue(
        self,
    ) -> list[dict[str, Any]]:
        if self.fail:
            raise ApiRequestError("API unavailable")

        return [
            {
                "id": "RPR000100",
                "customer_id": "CUS000100",
                "customer_name": "Remote Customer",
                "device_id": "DEV000100",
                "catalog_device_id": "CAT000100",
                "manufacturer": "Apple",
                "device_model": "iPhone",
                "repair_status": "In Repair",
                "problem_description": "Screen",
                "estimated_cost": 100.0,
                "final_cost": None,
                "intake_date": "2026-08-12",
                "technician": "Technician",
                "priority": "Urgent",
                "due_date": "",
            },
            {
                "id": "RPR000101",
                "customer_id": "CUS000101",
                "customer_name": "Completed Customer",
                "device_id": "DEV000101",
                "catalog_device_id": "",
                "manufacturer": "Samsung",
                "device_model": "Galaxy",
                "repair_status": "Completed",
                "problem_description": "",
                "estimated_cost": None,
                "final_cost": 50.0,
                "intake_date": "",
                "technician": "",
                "priority": "Urgent",
                "due_date": "",
            },
        ]


def test_offline_mode_uses_local_dashboard() -> None:
    local = FakeLocalService()

    service = ReadService(
        local_service=local,
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="offline",
        ),
        api_available=True,
    )

    counts = service.dashboard_counts()

    assert counts["customers"] == 1
    assert local.dashboard_calls == 1


def test_auto_online_uses_api_dashboard() -> None:
    local = FakeLocalService()

    service = ReadService(
        local_service=local,
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    counts = service.dashboard_counts()

    assert counts == {
        "customers": 10,
        "devices": 20,
        "repairs": 30,
        "open_repairs": 22,
    }

    assert local.dashboard_calls == 0


def test_auto_unavailable_uses_local_dashboard() -> None:
    local = FakeLocalService()

    service = ReadService(
        local_service=local,
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=False,
    )

    counts = service.dashboard_counts()

    assert counts["customers"] == 1
    assert local.dashboard_calls == 1


def test_auto_request_failure_falls_back_local() -> None:
    local = FakeLocalService()

    service = ReadService(
        local_service=local,
        api_client=FakeApiClient(fail=True),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    counts = service.dashboard_counts()

    assert counts["customers"] == 1
    assert local.dashboard_calls == 1


def test_online_unavailable_raises() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="online",
        ),
        api_available=False,
    )

    with pytest.raises(
        ReadServiceUnavailable,
        match="API is unavailable",
    ):
        service.dashboard_counts()


def test_operational_counts_use_remote_statuses() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    counts = service.dashboard_operational_counts()

    assert counts == {
        "awaiting_diagnosis": 2,
        "awaiting_approval": 3,
        "in_repair": 4,
        "awaiting_parts": 5,
        "ready_for_pickup": 6,
        "urgent_repairs": 1,
    }


def test_remote_queue_is_normalized_for_desktop() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    repairs = service.list_repairs()

    assert len(repairs) == 2

    first = repairs[0]

    assert first["ticket_id"] == "RPR000100"
    assert first["customer_id"] == "CUS000100"
    assert first["business_name"] == ("Remote Customer")
    assert first["manufacturer"] == "Apple"
    assert first["device_model"] == "iPhone"
    assert first["serial_number"] == ""
    assert first["priority"] == "Urgent"


def test_auto_queue_failure_falls_back_local() -> None:
    local = FakeLocalService()

    service = ReadService(
        local_service=local,
        api_client=FakeApiClient(fail=True),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    repairs = service.list_repairs()

    assert repairs[0]["ticket_id"] == ("LOCAL001")
    assert local.repair_calls == 1
