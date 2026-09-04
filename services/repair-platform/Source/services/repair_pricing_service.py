from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class RepairPricingValidationError(ValueError):
    """Raised when a repair-pricing item cannot be created safely."""


class RepairPricingNotFoundError(LookupError):
    """Raised when the repair or pricing record does not exist."""


class RepairPricingStateError(RuntimeError):
    """Raised when a pricing record is not eligible for repair selection."""


class RepairPricingService:
    def __init__(
        self,
        operations_database: Any,
    ) -> None:
        self.operations_database = operations_database

    def select_pricing_record(
        self,
        repair_id: str,
        pricing_record_id: str,
        *,
        quantity: int = 1,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        normalized_repair_id = repair_id.strip()
        normalized_pricing_record_id = pricing_record_id.strip()

        if not normalized_repair_id:
            raise RepairPricingValidationError("repair_id is required.")

        if not normalized_pricing_record_id:
            raise RepairPricingValidationError("pricing_record_id is required.")

        if quantity <= 0:
            raise RepairPricingValidationError("quantity must be greater than zero.")

        repair = self.operations_database.get_repair(normalized_repair_id)

        if repair is None:
            raise RepairPricingNotFoundError(
                f"Repair {normalized_repair_id!r} was not found."
            )

        pricing_record = self.operations_database.get_service_pricing_record(
            normalized_pricing_record_id
        )

        if pricing_record is None:
            raise RepairPricingNotFoundError(
                f"Pricing record {normalized_pricing_record_id!r} was not found."
            )
        repair_device = self.operations_database.get_customer_device(
            str(repair["device_id"])
        )

        if repair_device is None:
            raise RepairPricingStateError(
                f"Repair {normalized_repair_id!r} does not have a valid device."
            )

        repair_catalog_device_id = str(
            repair_device.get("catalog_device_id") or ""
        ).strip()
        pricing_catalog_device_id = str(
            pricing_record.get("catalog_device_id") or ""
        ).strip()

        if repair_catalog_device_id != pricing_catalog_device_id:
            raise RepairPricingStateError(
                f"Pricing record {normalized_pricing_record_id!r} "
                f"is for catalog device {pricing_catalog_device_id!r}, "
                f"not repair device {repair_catalog_device_id!r}."
            )

        if pricing_record["approval_status"] != "APPROVED":
            raise RepairPricingStateError(
                f"Pricing record {normalized_pricing_record_id!r} is not APPROVED."
            )

        approved_price_cents = pricing_record["approved_price_cents"]

        if approved_price_cents is None:
            raise RepairPricingStateError(
                f"Pricing record "
                f"{normalized_pricing_record_id!r} "
                "does not have an approved price."
            )

        timestamp = now if now is not None else datetime.now(UTC)

        if timestamp.tzinfo is None:
            raise RepairPricingValidationError("now must be timezone-aware.")

        timestamp_text = timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")

        repair_pricing_item_id = self.operations_database.next_id(
            table="repair_pricing_items",
            column="repair_pricing_item_id",
            prefix="RPI",
            width=6,
        )

        unit_price_cents = int(approved_price_cents)
        line_total_cents = unit_price_cents * quantity

        record = {
            "repair_pricing_item_id": repair_pricing_item_id,
            "repair_id": normalized_repair_id,
            "pricing_record_id": normalized_pricing_record_id,
            "service_type_id": pricing_record["service_type_id"],
            "variant_key": pricing_record["variant_key"],
            "service_type": pricing_record["service_type"],
            "quality_class": pricing_record["quality_class"],
            "customer_facing_tier": pricing_record["customer_facing_tier"],
            "supplier": pricing_record["supplier"],
            "supplier_product_id": pricing_record["supplier_product_id"],
            "supplier_sku": pricing_record["supplier_sku"],
            "part_name": pricing_record["part_name"],
            "quoted_unit_price_cents": unit_price_cents,
            "quantity": quantity,
            "line_total_cents": line_total_cents,
            "pricing_snapshot_at": timestamp_text,
            "created_at": timestamp_text,
            "updated_at": timestamp_text,
        }

        return self.operations_database.create_repair_pricing_item(record)

    def list_items(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        normalized_repair_id = repair_id.strip()

        if not normalized_repair_id:
            raise RepairPricingValidationError("repair_id is required.")

        repair = self.operations_database.get_repair(normalized_repair_id)

        if repair is None:
            raise RepairPricingNotFoundError(
                f"Repair {normalized_repair_id!r} was not found."
            )

        return self.operations_database.list_repair_pricing_items(normalized_repair_id)
