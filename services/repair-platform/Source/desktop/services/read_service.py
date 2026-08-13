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

    def get_repair_workspace(
        self,
        ticket_id: str,
    ) -> dict[str, Any] | None: ...
    def list_repair_checkins(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]: ...

    def list_repair_events(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]: ...


class ApiReadProvider(Protocol):
    def dashboard(
        self,
    ) -> dict[str, Any]: ...

    def repair_queue(
        self,
    ) -> list[dict[str, Any]]: ...

    def get_repair(
        self,
        repair_id: str,
    ) -> dict[str, Any]: ...
    def list_repair_events(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]: ...

    def get_repair_checkin(
        self,
        repair_id: str,
    ) -> dict[str, Any]: ...


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

    def get_repair_workspace(
        self,
        repair_id: str,
    ) -> dict[str, Any] | None:
        if not self._should_use_api():
            return self.local_service.get_repair_workspace(repair_id)

        try:
            repair = self.api_client.get_repair(repair_id)

        except ApiRequestError as exc:
            if self._fallback_allowed():
                return self.local_service.get_repair_workspace(repair_id)

            raise ReadServiceUnavailable(str(exc)) from exc

        return self._normalize_repair(repair)

    def list_repair_events(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        if not self._should_use_api():
            return self.local_service.list_repair_events(repair_id)

        try:
            events = self.api_client.list_repair_events(repair_id)

        except ApiRequestError as exc:
            if self._fallback_allowed():
                return self.local_service.list_repair_events(repair_id)

            raise ReadServiceUnavailable(str(exc)) from exc

        return [dict(event) for event in events]

    def list_repair_checkins(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        if not self._should_use_api():
            return self.local_service.list_repair_checkins(repair_id)

        try:
            checkin = self.api_client.get_repair_checkin(repair_id)

        except ApiRequestError as exc:
            if self._fallback_allowed():
                return self.local_service.list_repair_checkins(repair_id)

            raise ReadServiceUnavailable(str(exc)) from exc

        return [self._normalize_checkin(checkin)]

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

    @staticmethod
    def _normalize_repair(
        repair: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = dict(repair)

        repair_id = str(
            repair.get(
                "id",
                repair.get(
                    "ticket_id",
                    "",
                ),
            )
            or ""
        )

        normalized["ticket_id"] = (
            repair_id
        )

        if "id" not in normalized:
            normalized["id"] = (
                repair_id
            )

        normalized.setdefault(
            "customer_id",
            "",
        )
        normalized.setdefault(
            "device_id",
            "",
        )
        normalized.setdefault(
            "repair_status",
            "",
        )
        normalized.setdefault(
            "intake_date",
            "",
        )
        normalized.setdefault(
            "technician",
            "",
        )
        normalized.setdefault(
            "priority",
            "Normal",
        )
        normalized.setdefault(
            "due_date",
            "",
        )
        normalized.setdefault(
            "problem_description",
            "",
        )
        normalized.setdefault(
            "diagnosis",
            "",
        )
        normalized.setdefault(
            "estimated_cost",
            None,
        )
        normalized.setdefault(
            "final_cost",
            None,
        )
        normalized.setdefault(
            "date_completed",
            "",
        )
        normalized.setdefault(
            "date_picked_up",
            "",
        )
        normalized.setdefault(
            "warranty",
            False,
        )
        normalized.setdefault(
            "notes",
            "",
        )
        normalized.setdefault(
            "last_modified",
            "",
        )

        normalized.setdefault(
            "customer_type",
            "",
        )
        normalized.setdefault(
            "first_name",
            "",
        )
        normalized.setdefault(
            "last_name",
            "",
        )
        normalized.setdefault(
            "business_name",
            "",
        )
        normalized.setdefault(
            "email",
            "",
        )
        normalized.setdefault(
            "mobile_phone",
            "",
        )
        normalized.setdefault(
            "preferred_contact",
            "",
        )

        normalized.setdefault(
            "catalog_device_id",
            "",
        )
        normalized.setdefault(
            "manufacturer",
            "",
        )
        normalized.setdefault(
            "device_family",
            "",
        )
        normalized.setdefault(
            "device_model",
            "",
        )
        normalized.setdefault(
            "serial_number",
            "",
        )
        normalized.setdefault(
            "imei_service_tag",
            "",
        )
        normalized.setdefault(
            "color",
            "",
        )
        normalized.setdefault(
            "storage",
            "",
        )
        normalized.setdefault(
            "carrier",
            "",
        )

        return normalized

    @staticmethod
    def _normalize_checkin(
        checkin: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = dict(checkin)

        checkin_id = str(
            checkin.get(
                "id",
                checkin.get(
                    "checkin_id",
                    "",
                ),
            )
            or ""
        )

        normalized["checkin_id"] = checkin_id

        if "id" not in normalized:
            normalized["id"] = checkin_id

        return normalized
