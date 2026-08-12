from __future__ import annotations

from typing import Any, Protocol

from desktop.services.api_client import (
    ApiRequestError,
)
from desktop.services.settings_service import (
    DesktopSettings,
)

CLOSED_REPAIR_STATUSES = {
    "Completed",
    "Picked Up",
    "Cancelled",
}


class LocalReadProvider(Protocol):
    def dashboard_counts(
        self,
    ) -> dict[str, int]: ...

    def dashboard_operational_counts(
        self,
    ) -> dict[str, int]: ...

    def list_repairs(
        self,
        limit: int = 500,
    ) -> list[dict[str, Any]]: ...


class ApiReadProvider(Protocol):
    def dashboard(
        self,
    ) -> dict[str, Any]: ...

    def repair_queue(
        self,
    ) -> list[dict[str, Any]]: ...


class ReadServiceUnavailable(RuntimeError):
    pass


class ReadService:
    def __init__(
        self,
        *,
        local_service: LocalReadProvider,
        api_client: ApiReadProvider,
        settings: DesktopSettings,
        api_available: bool,
    ) -> None:
        self.local_service = local_service
        self.api_client = api_client
        self.settings = settings
        self.api_available = api_available

    def _should_use_api(
        self,
    ) -> bool:
        mode = self.settings.connection_mode

        if mode == "offline":
            return False

        if self.api_available:
            return True

        if mode == "auto":
            return False

        raise ReadServiceUnavailable(
            "Online mode is enabled, but " "the Nocturnix API is unavailable."
        )

    def _fallback_allowed(
        self,
    ) -> bool:
        return self.settings.connection_mode == "auto"

    def dashboard_counts(
        self,
    ) -> dict[str, int]:
        if not self._should_use_api():
            return self.local_service.dashboard_counts()

        try:
            payload = self.api_client.dashboard()
        except ApiRequestError as exc:
            if self._fallback_allowed():
                return self.local_service.dashboard_counts()

            raise ReadServiceUnavailable(str(exc)) from exc

        repairs_by_status = self._repairs_by_status(payload)

        repairs = self._integer(
            payload.get(
                "repairs",
                0,
            )
        )

        closed_repairs = sum(
            repairs_by_status.get(
                status,
                0,
            )
            for status in CLOSED_REPAIR_STATUSES
        )

        return {
            "customers": self._integer(
                payload.get(
                    "customers",
                    0,
                )
            ),
            "devices": self._integer(
                payload.get(
                    "devices",
                    0,
                )
            ),
            "repairs": repairs,
            "open_repairs": max(
                repairs - closed_repairs,
                0,
            ),
        }

    def dashboard_operational_counts(
        self,
    ) -> dict[str, int]:
        if not self._should_use_api():
            return self.local_service.dashboard_operational_counts()

        try:
            payload = self.api_client.dashboard()

            queue = self.api_client.repair_queue()

        except ApiRequestError as exc:
            if self._fallback_allowed():
                return self.local_service.dashboard_operational_counts()

            raise ReadServiceUnavailable(str(exc)) from exc

        repairs_by_status = self._repairs_by_status(payload)

        urgent_repairs = 0

        for repair in queue:
            priority = str(
                repair.get(
                    "priority",
                    "",
                )
                or ""
            ).strip()

            status = str(
                repair.get(
                    "repair_status",
                    "",
                )
                or ""
            ).strip()

            if priority == "Urgent" and status not in CLOSED_REPAIR_STATUSES:
                urgent_repairs += 1

        return {
            "awaiting_diagnosis": (
                repairs_by_status.get(
                    "Awaiting Diagnosis",
                    0,
                )
            ),
            "awaiting_approval": (
                repairs_by_status.get(
                    "Awaiting Approval",
                    0,
                )
            ),
            "in_repair": (
                repairs_by_status.get(
                    "In Repair",
                    0,
                )
            ),
            "awaiting_parts": (
                repairs_by_status.get(
                    "Awaiting Parts",
                    0,
                )
            ),
            "ready_for_pickup": (
                repairs_by_status.get(
                    "Ready for Pickup",
                    0,
                )
            ),
            "urgent_repairs": (urgent_repairs),
        }

    def list_repairs(
        self,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        if not self._should_use_api():
            return self.local_service.list_repairs(limit=limit)

        try:
            queue = self.api_client.repair_queue()
        except ApiRequestError as exc:
            if self._fallback_allowed():
                return self.local_service.list_repairs(limit=limit)

            raise ReadServiceUnavailable(str(exc)) from exc

        normalized = [self._normalize_queue_item(item) for item in queue]

        return normalized[:limit]

    @staticmethod
    def _normalize_queue_item(
        item: dict[str, Any],
    ) -> dict[str, Any]:
        customer_name = str(
            item.get(
                "customer_name",
                "",
            )
            or ""
        ).strip()

        return {
            "ticket_id": str(
                item.get(
                    "id",
                    "",
                )
                or ""
            ),
            "customer_id": str(
                item.get(
                    "customer_id",
                    "",
                )
                or ""
            ),
            "device_id": str(
                item.get(
                    "device_id",
                    "",
                )
                or ""
            ),
            "catalog_device_id": str(
                item.get(
                    "catalog_device_id",
                    "",
                )
                or ""
            ),
            "first_name": "",
            "last_name": "",
            "business_name": (customer_name),
            "customer_name": (customer_name),
            "manufacturer": str(
                item.get(
                    "manufacturer",
                    "",
                )
                or ""
            ),
            "device_family": "",
            "device_model": str(
                item.get(
                    "device_model",
                    "",
                )
                or ""
            ),
            "serial_number": "",
            "repair_status": str(
                item.get(
                    "repair_status",
                    "",
                )
                or ""
            ),
            "problem_description": str(
                item.get(
                    "problem_description",
                    "",
                )
                or ""
            ),
            "estimated_cost": item.get("estimated_cost"),
            "final_cost": item.get("final_cost"),
            "intake_date": str(
                item.get(
                    "intake_date",
                    "",
                )
                or ""
            ),
            "technician": str(
                item.get(
                    "technician",
                    "",
                )
                or ""
            ),
            "priority": str(
                item.get(
                    "priority",
                    "Normal",
                )
                or "Normal"
            ),
            "due_date": str(
                item.get(
                    "due_date",
                    "",
                )
                or ""
            ),
        }

    @staticmethod
    def _repairs_by_status(
        payload: dict[str, Any],
    ) -> dict[str, int]:
        raw = payload.get(
            "repairs_by_status",
            {},
        )

        if not isinstance(
            raw,
            dict,
        ):
            return {}

        return {str(key): ReadService._integer(value) for key, value in raw.items()}

    @staticmethod
    def _integer(
        value: Any,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0
