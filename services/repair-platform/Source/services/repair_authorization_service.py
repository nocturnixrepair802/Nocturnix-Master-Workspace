from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class RepairAuthorizationValidationError(ValueError):
    """Raised when an authorization request is invalid."""


class RepairAuthorizationNotFoundError(LookupError):
    """Raised when an authorization or related repair resource is missing."""


class RepairAuthorizationStateError(RuntimeError):
    """Raised when an authorization state transition is not allowed."""


class RepairAuthorizationService:
    STATUS_PENDING = "PENDING"
    STATUS_AUTHORIZED = "AUTHORIZED"
    STATUS_DECLINED = "DECLINED"

    def __init__(
        self,
        operations_database: Any,
    ) -> None:
        self.operations_database = operations_database

    def create(
        self,
        repair_id: str,
        repair_pricing_item_ids: list[str],
        *,
        terms_document_id: str = "",
        terms_version: str = "",
        created_by: str = "Ryan Brown",
        now: datetime | None = None,
    ) -> dict[str, Any]:
        normalized_repair_id = repair_id.strip()

        if not normalized_repair_id:
            raise RepairAuthorizationValidationError("repair_id is required.")

        repair = self.operations_database.get_repair(normalized_repair_id)

        if repair is None:
            raise RepairAuthorizationNotFoundError(
                f"Repair {normalized_repair_id!r} was not found."
            )

        normalized_item_ids = [
            item_id.strip() for item_id in repair_pricing_item_ids if item_id.strip()
        ]

        if not normalized_item_ids:
            raise RepairAuthorizationValidationError(
                "At least one repair pricing item is required."
            )

        if len(normalized_item_ids) != len(set(normalized_item_ids)):
            raise RepairAuthorizationValidationError(
                "Duplicate repair pricing item IDs are not allowed."
            )

        pricing_items: list[dict[str, Any]] = []

        for repair_pricing_item_id in normalized_item_ids:
            item = self.operations_database.get_repair_pricing_item(
                repair_pricing_item_id
            )

            if item is None:
                raise RepairAuthorizationNotFoundError(
                    f"Repair pricing item {repair_pricing_item_id!r} was not found."
                )

            if str(item["repair_id"]) != normalized_repair_id:
                raise RepairAuthorizationValidationError(
                    f"Repair pricing item "
                    f"{repair_pricing_item_id!r} "
                    f"does not belong to repair "
                    f"{normalized_repair_id!r}."
                )

            pricing_items.append(item)

        quoted_total_cents = sum(
            int(item["line_total_cents"]) for item in pricing_items
        )

        timestamp = now if now is not None else datetime.now(UTC)

        if timestamp.tzinfo is None:
            raise RepairAuthorizationValidationError("now must be timezone-aware.")

        timestamp_text = timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")

        authorization_id = self.operations_database.next_id(
            table="repair_authorizations",
            column="authorization_id",
            prefix="AUT",
            width=6,
        )

        record = {
            "authorization_id": authorization_id,
            "repair_id": normalized_repair_id,
            "authorization_type": "REPAIR_QUOTE",
            "authorization_status": self.STATUS_PENDING,
            "quoted_total_cents": quoted_total_cents,
            "currency": "USD",
            "terms_document_id": terms_document_id.strip(),
            "terms_version": terms_version.strip(),
            "customer_name": "",
            "authorization_method": "",
            "authorized_at": None,
            "declined_at": None,
            "created_at": timestamp_text,
            "updated_at": timestamp_text,
            "created_by": created_by.strip() or "Ryan Brown",
        }

        return self.operations_database.create_repair_authorization(
            record,
            [str(item["repair_pricing_item_id"]) for item in pricing_items],
        )
