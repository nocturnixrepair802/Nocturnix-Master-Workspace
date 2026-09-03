from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from models.service_pricing import ServicePricingPreview
from models.service_pricing_catalog import ServicePricingCatalogRecord


class ServicePricingCatalogValidationError(ValueError):
    """Raised when a pricing snapshot cannot be persisted safely."""


class ServicePricingCatalogService:
    """
    Persist calculated service-pricing snapshots.

    This service does not:

    - calculate pricing;
    - select supplier products;
    - call Mobile Sentrix;
    - read pricing workbooks;
    - approve customer-facing prices;
    - place supplier orders.

    Pricing calculations must already have been produced by
    ServicePricingService.
    """

    def __init__(
        self,
        operations_database: Any,
    ) -> None:
        self.operations_database = operations_database

    def create_from_preview(
        self,
        preview: ServicePricingPreview,
        *,
        supplier_observed_at: datetime | None = None,
        now: datetime | None = None,
    ) -> ServicePricingCatalogRecord:
        timestamp = now if now is not None else datetime.now(UTC)

        if timestamp.tzinfo is None:
            raise ServicePricingCatalogValidationError("now must be timezone-aware.")

        observed_at = supplier_observed_at

        if observed_at is not None and observed_at.tzinfo is None:
            raise ServicePricingCatalogValidationError(
                "supplier_observed_at must be timezone-aware."
            )

        pricing_record_id = self.operations_database.next_id(
            table="service_pricing_catalog",
            column="pricing_record_id",
            prefix="PRC",
            width=6,
        )

        record = {
            "pricing_record_id": pricing_record_id,
            "catalog_device_id": preview.device_id,
            "service_type_id": preview.service_type_id,
            "service_type": preview.service_type,
            "service_category_id": (preview.service_category_id),
            "variant_key": preview.variant_key,
            "variant_name": preview.variant_name,
            "supplier": preview.supplier,
            "supplier_product_id": (preview.supplier_product_id),
            "supplier_sku": preview.supplier_sku,
            "part_name": preview.part_name,
            "part_cost_cents": self._money_to_cents(preview.part_cost),
            "supplier_in_stock": (
                None
                if preview.supplier_in_stock is None
                else int(preview.supplier_in_stock)
            ),
            "supplier_stock_qty": (preview.supplier_stock_qty),
            "supplier_observed_at": (self._datetime_to_text(observed_at)),
            "default_labor_hours": self._decimal_to_text(preview.default_labor_hours),
            "labor_profile_id": (preview.labor_profile_id),
            "labor_tier": preview.labor_tier,
            "hourly_rate_cents": self._money_to_cents(preview.hourly_rate),
            "minimum_charge_cents": (self._money_to_cents(preview.minimum_charge)),
            "target_margin": self._decimal_to_text(preview.target_margin),
            "minimum_margin": self._decimal_to_text(preview.minimum_margin),
            "overhead_rate": self._decimal_to_text(preview.overhead_rate),
            "warranty_rate": self._decimal_to_text(preview.warranty_rate),
            "risk_rate": self._decimal_to_text(preview.risk_rate),
            "processing_rate": self._decimal_to_text(preview.processing_rate),
            "rounding_rule": preview.rounding_rule,
            "billable_labor_cost_cents": (
                self._money_to_cents(preview.billable_labor_cost)
            ),
            "shipping_cents": self._money_to_cents(preview.shipping),
            "consumables_cents": (self._money_to_cents(preview.consumables)),
            "base_direct_cost_cents": (self._money_to_cents(preview.base_direct_cost)),
            "total_internal_cost_cents": (
                self._money_to_cents(preview.total_internal_cost)
            ),
            "recommended_price_cents": (
                self._money_to_cents(preview.recommended_retail_price)
            ),
            "gross_profit_cents": (self._money_to_cents(preview.gross_profit)),
            "gross_margin": self._decimal_to_text(preview.gross_margin),
            "pricing_status": preview.pricing_status,
            "approved_price_cents": None,
            "approval_status": "DRAFT",
            "approved_at": None,
            "approved_by": None,
            "created_at": self._datetime_to_text(timestamp),
            "updated_at": self._datetime_to_text(timestamp),
        }

        self.operations_database.create_service_pricing_record(record)

        return self._record_from_storage(record)

    @staticmethod
    def _money_to_cents(
        value: Decimal,
    ) -> int:
        cents = (Decimal(value) * Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )

        return int(cents)

    @staticmethod
    def _decimal_to_text(
        value: Decimal,
    ) -> str:
        return str(Decimal(value))

    @staticmethod
    def _datetime_to_text(
        value: datetime | None,
    ) -> str | None:
        if value is None:
            return None

        return (
            value.astimezone(UTC)
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

    @staticmethod
    def _datetime_from_text(
        value: str | None,
    ) -> datetime | None:
        if value is None:
            return None

        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

    @classmethod
    def _record_from_storage(
        cls,
        record: dict[str, Any],
    ) -> ServicePricingCatalogRecord:
        return ServicePricingCatalogRecord(
            pricing_record_id=str(record["pricing_record_id"]),
            catalog_device_id=str(record["catalog_device_id"]),
            service_type_id=str(record["service_type_id"]),
            service_type=str(record["service_type"]),
            service_category_id=str(record["service_category_id"]),
            variant_key=str(record["variant_key"]),
            variant_name=record["variant_name"],
            supplier=str(record["supplier"]),
            supplier_product_id=str(record["supplier_product_id"]),
            supplier_sku=str(record["supplier_sku"]),
            part_name=str(record["part_name"]),
            part_cost=Decimal(record["part_cost_cents"]) / Decimal("100"),
            supplier_in_stock=(
                None
                if record["supplier_in_stock"] is None
                else bool(record["supplier_in_stock"])
            ),
            supplier_stock_qty=(record["supplier_stock_qty"]),
            supplier_observed_at=(
                cls._datetime_from_text(record["supplier_observed_at"])
            ),
            default_labor_hours=Decimal(record["default_labor_hours"]),
            labor_profile_id=str(record["labor_profile_id"]),
            labor_tier=str(record["labor_tier"]),
            hourly_rate=Decimal(record["hourly_rate_cents"]) / Decimal("100"),
            minimum_charge=Decimal(record["minimum_charge_cents"]) / Decimal("100"),
            target_margin=Decimal(record["target_margin"]),
            minimum_margin=Decimal(record["minimum_margin"]),
            overhead_rate=Decimal(record["overhead_rate"]),
            warranty_rate=Decimal(record["warranty_rate"]),
            risk_rate=Decimal(record["risk_rate"]),
            processing_rate=Decimal(record["processing_rate"]),
            rounding_rule=str(record["rounding_rule"]),
            billable_labor_cost=Decimal(record["billable_labor_cost_cents"])
            / Decimal("100"),
            shipping=Decimal(record["shipping_cents"]) / Decimal("100"),
            consumables=Decimal(record["consumables_cents"]) / Decimal("100"),
            base_direct_cost=Decimal(record["base_direct_cost_cents"]) / Decimal("100"),
            total_internal_cost=Decimal(record["total_internal_cost_cents"])
            / Decimal("100"),
            recommended_price=Decimal(record["recommended_price_cents"])
            / Decimal("100"),
            gross_profit=Decimal(record["gross_profit_cents"]) / Decimal("100"),
            gross_margin=Decimal(record["gross_margin"]),
            pricing_status=str(record["pricing_status"]),
            approved_price=(
                None
                if record["approved_price_cents"] is None
                else Decimal(record["approved_price_cents"]) / Decimal("100")
            ),
            approval_status=str(record["approval_status"]),
            approved_at=cls._datetime_from_text(record["approved_at"]),
            approved_by=record["approved_by"],
            created_at=(
                cls._datetime_from_text(record["created_at"])
                or datetime.min.replace(tzinfo=UTC)
            ),
            updated_at=(
                cls._datetime_from_text(record["updated_at"])
                or datetime.min.replace(tzinfo=UTC)
            ),
        )
