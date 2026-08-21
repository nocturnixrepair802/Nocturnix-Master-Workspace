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

    def get_repair_workspace(
        self,
        ticket_id: str,
    ) -> dict[str, Any] | None:
        return {
            "ticket_id": ticket_id,
            "source": "local",
        }

    def list_repair_events(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        return [
            {
                "event_id": "LOCAL_EVENT",
                "repair_id": repair_id,
                "event_type": "local_event",
                "created_at": "2026-08-12",
            }
        ]

    def list_repair_checkins(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        return [
            {
                "checkin_id": "LOCAL_CHECKIN",
                "repair_id": repair_id,
                "technician": "Local Technician",
            }
        ]


class FakePaymentService:
    def list_repair_payments(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        return [
            {
                "payment_id": "LOCAL_PAYMENT",
                "repair_id": repair_id,
                "payment_method": "Cash",
                "payment_status": "Completed",
                "amount": 25.0,
            }
        ]

    def payment_summary(
        self,
        repair_id: str,
    ) -> dict[str, Any]:
        return {
            "repair_id": repair_id,
            "repair_status": "In Repair",
            "final_cost": 100.0,
            "amount_paid": 25.0,
            "balance_due": 75.0,
            "payment_status": "Partially Paid",
            "currency": "USD",
            "source": "local",
        }


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

    def get_repair(
        self,
        repair_id: str,
    ) -> dict[str, Any]:
        if self.fail:
            raise ApiRequestError("API unavailable")

        return {
            "id": repair_id,
            "customer_id": "CUS000100",
            "device_id": "DEV000100",
            "repair_status": "In Repair",
            "priority": "Normal",
        }

    def list_repair_events(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        if self.fail:
            raise ApiRequestError("API unavailable")

        return [
            {
                "event_id": "EVT000001",
                "repair_id": repair_id,
                "event_type": "repair_created",
                "old_value": "",
                "new_value": "New Intake",
                "notes": "",
                "created_at": "2026-08-12T10:00:00",
                "created_by": "Ryan Brown",
            }
        ]

    def get_repair_checkin(
        self,
        repair_id: str,
    ) -> dict[str, Any]:
        if self.fail:
            raise ApiRequestError("API unavailable")

        return {
            "id": "CHK000001",
            "repair_id": repair_id,
            "customer_id": "CUS000100",
            "device_id": "DEV000100",
            "technician": "Ryan Brown",
            "checkin_timestamp": ("2026-08-12T10:00:00"),
            "powers_on": "Yes",
            "battery_percentage": 75,
            "liquid_damage": "No",
            "intake_notes": "Remote check-in",
        }

    def list_repair_payments(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        if self.fail:
            raise ApiRequestError("API unavailable")

        return [
            {
                "payment_id": "PAY000100",
                "repair_id": repair_id,
                "payment_method": "Square",
                "payment_status": "Completed",
                "amount": 60.0,
                "currency": "USD",
                "payment_timestamp": ("2026-08-12T15:00:00"),
                "reference_number": "",
                "square_payment_id": "SQPAY100",
            }
        ]

    def repair_payment_summary(
        self,
        repair_id: str,
    ) -> dict[str, Any]:
        if self.fail:
            raise ApiRequestError("API unavailable")

        return {
            "repair_id": repair_id,
            "repair_status": "In Repair",
            "final_cost": 100.0,
            "amount_paid": 60.0,
            "balance_due": 40.0,
            "payment_status": "Partially Paid",
            "currency": "USD",
            "source": "remote",
        }


def test_offline_mode_uses_local_dashboard() -> None:
    local = FakeLocalService()

    service = ReadService(
        local_service=local,
        local_payment_service=FakePaymentService(),
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
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
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
        local_payment_service=FakePaymentService(),
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
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(
            fail=True,
        ),
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
        local_payment_service=FakePaymentService(),
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
        local_payment_service=FakePaymentService(),
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
        local_payment_service=FakePaymentService(),
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
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(
            fail=True,
        ),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    repairs = service.list_repairs()

    assert repairs[0]["ticket_id"] == ("LOCAL001")
    assert local.repair_calls == 1


def test_remote_repair_detail_is_normalized() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    repair = service.get_repair_workspace("RPR000100")

    assert repair is not None
    assert repair["ticket_id"] == "RPR000100"
    assert repair["customer_id"] == "CUS000100"
    assert repair["device_id"] == "DEV000100"


def test_offline_repair_detail_uses_local() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="offline",
        ),
        api_available=True,
    )

    repair = service.get_repair_workspace("LOCAL001")

    assert repair is not None
    assert repair["source"] == "local"


def test_auto_repair_detail_failure_falls_back_local() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(
            fail=True,
        ),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    repair = service.get_repair_workspace("LOCAL002")

    assert repair is not None
    assert repair["source"] == "local"


def test_online_repair_detail_failure_raises() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(
            fail=True,
        ),
        settings=DesktopSettings(
            connection_mode="online",
        ),
        api_available=True,
    )

    with pytest.raises(
        ReadServiceUnavailable,
    ):
        service.get_repair_workspace("RPR000100")


def test_remote_repair_events_use_api() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    events = service.list_repair_events("RPR000100")

    assert len(events) == 1
    assert events[0]["event_id"] == ("EVT000001")
    assert events[0]["repair_id"] == ("RPR000100")


def test_auto_repair_events_failure_falls_back_local() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(
            fail=True,
        ),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    events = service.list_repair_events("RPR000100")

    assert events[0]["event_id"] == ("LOCAL_EVENT")


def test_remote_repair_checkin_is_normalized() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    checkins = service.list_repair_checkins("RPR000100")

    assert len(checkins) == 1
    assert checkins[0]["checkin_id"] == ("CHK000001")
    assert checkins[0]["repair_id"] == ("RPR000100")
    assert checkins[0]["battery_percentage"] == 75


def test_auto_repair_checkin_failure_falls_back_local() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(
            fail=True,
        ),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    checkins = service.list_repair_checkins("RPR000100")

    assert checkins[0]["checkin_id"] == ("LOCAL_CHECKIN")


def test_remote_repair_payments_use_api() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    payments = service.list_repair_payments("RPR000100")

    assert len(payments) == 1
    assert payments[0]["payment_id"] == ("PAY000100")


def test_auto_payment_history_failure_falls_back_local() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(fail=True),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    payments = service.list_repair_payments("RPR000100")

    assert payments[0]["payment_id"] == ("LOCAL_PAYMENT")


def test_remote_payment_summary_uses_api() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    summary = service.payment_summary("RPR000100")

    assert summary["source"] == "remote"
    assert summary["amount_paid"] == 60.0
    assert summary["balance_due"] == 40.0


def test_auto_payment_summary_failure_falls_back_local() -> None:
    service = ReadService(
        local_service=FakeLocalService(),
        local_payment_service=FakePaymentService(),
        api_client=FakeApiClient(fail=True),
        settings=DesktopSettings(
            connection_mode="auto",
        ),
        api_available=True,
    )

    summary = service.payment_summary("RPR000100")

    assert summary["source"] == "local"
    assert summary["amount_paid"] == 25.0
