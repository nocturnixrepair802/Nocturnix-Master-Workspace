from __future__ import annotations

from decimal import Decimal
from typing import Any

from engines.pricing_engine import PricingEngine
from integrations.mobilesentrix.models import (
    MobileSentrixDetailedProduct,
    MobileSentrixProduct,
)
from models.service_pricing import ServicePricingPreview
from services.pricing_rule_provider import PricingRuleProvider


class ServicePricingValidationError(ValueError):
    """Raised when a pricing preview cannot be assembled safely."""


class ServicePricingNotFoundError(LookupError):
    """Raised when a requested Nocturnix catalog entity does not exist."""


class ServicePricingService:
    """
    Assemble a read-only Nocturnix service pricing preview.

    Responsibilities:

    - Resolve the Nocturnix device.
    - Resolve a supplied Service Type ID through PricingRuleProvider.
    - Accept a user-selected normalized Mobile Sentrix product.
    - Preserve supplier product identifiers.
    - Delegate pricing mathematics to PricingEngine.

    This service does not:

    - write to the catalog database;
    - write pricing approvals;
    - select supplier products automatically;
    - place supplier orders;
    - call Mobile Sentrix directly;
    - read Calculation Master directly.
    """

    def __init__(
        self,
        catalog_database: Any,
        pricing_rule_provider: PricingRuleProvider,
        pricing_engine: PricingEngine | None = None,
    ) -> None:
        self.catalog_database = catalog_database
        self.pricing_rule_provider = pricing_rule_provider
        self.pricing_engine = pricing_engine or PricingEngine()

    def preview(
        self,
        *,
        device_id: str,
        service_type_id: str,
        product: MobileSentrixProduct | MobileSentrixDetailedProduct,
        shipping: Decimal | float | int | str = Decimal("0.00"),
        consumables: Decimal | float | int | str = Decimal("5.00"),
    ) -> ServicePricingPreview:
        """
        Build a read-only service pricing preview.
        """

        resolved_device_id = str(device_id).strip()

        if not resolved_device_id:
            raise ServicePricingValidationError("device_id is required.")

        self._validate_service_type_id(service_type_id)

        rule = self.pricing_rule_provider.get(service_type_id)

        device = self.catalog_database.get_device(resolved_device_id)

        if device is None:
            raise ServicePricingNotFoundError(
                f"Catalog device not found: {resolved_device_id}"
            )

        supplier_data = self._supplier_data(product)

        resolved_shipping = Decimal(str(shipping))
        resolved_consumables = Decimal(str(consumables))

        calculation = self.pricing_engine.calculate(
            part_cost=supplier_data["part_cost"],
            default_labor_hours=rule.default_labor_hours,
            hourly_rate=rule.hourly_rate,
            minimum_charge=rule.minimum_charge,
            shipping=resolved_shipping,
            consumables=resolved_consumables,
            overhead_rate=rule.overhead_rate,
            warranty_rate=rule.warranty_rate,
            risk_rate=rule.risk_rate,
            processing_rate=rule.processing_rate,
            target_margin=rule.target_margin,
            minimum_margin=rule.minimum_margin,
        )

        return ServicePricingPreview(
            device_id=str(device.get("device_id") or ""),
            device_model=str(device.get("device_model") or ""),
            manufacturer_id=str(device.get("manufacturer_id") or ""),
            manufacturer=str(device.get("manufacturer") or ""),
            service_type_id=rule.service_type_id,
            service_type=rule.service_type,
            service_category_id=rule.service_category_id,
            supplier=supplier_data["supplier"],
            supplier_product_id=supplier_data["supplier_product_id"],
            supplier_sku=supplier_data["supplier_sku"],
            part_name=supplier_data["part_name"],
            part_cost=calculation["part_cost"],
            supplier_in_stock=supplier_data["supplier_in_stock"],
            supplier_stock_qty=supplier_data["supplier_stock_qty"],
            default_labor_hours=calculation["default_labor_hours"],
            labor_profile_id=rule.labor_profile_id,
            labor_tier=rule.labor_tier,
            hourly_rate=calculation["hourly_rate"],
            minimum_charge=calculation["minimum_charge"],
            calculated_labor_cost=calculation["calculated_labor_cost"],
            billable_labor_cost=calculation["billable_labor_cost"],
            shipping=calculation["shipping"],
            consumables=calculation["consumables"],
            base_direct_cost=calculation["base_direct_cost"],
            overhead_rate=calculation["overhead_rate"],
            overhead_reserve=calculation["overhead_reserve"],
            warranty_rate=calculation["warranty_rate"],
            warranty_reserve=calculation["warranty_reserve"],
            risk_rate=calculation["risk_rate"],
            risk_reserve=calculation["risk_reserve"],
            processing_rate=calculation["processing_rate"],
            processing_reserve=calculation["processing_reserve"],
            total_internal_cost=calculation["total_internal_cost"],
            target_margin=calculation["target_margin"],
            minimum_margin=calculation["minimum_margin"],
            raw_retail_price=calculation["raw_retail_price"],
            recommended_retail_price=calculation["recommended_retail_price"],
            gross_profit=calculation["gross_profit"],
            gross_margin=calculation["gross_margin"],
            pricing_status=calculation["pricing_status"],
        )

    @staticmethod
    def _validate_service_type_id(
        service_type_id: str,
    ) -> None:
        value = str(service_type_id).strip()

        if len(value) != 9 or not value.startswith("STY") or not value[3:].isdigit():
            raise ServicePricingValidationError(
                "service_type_id must use the governed " "STY###### format."
            )

    @staticmethod
    def _supplier_data(
        product: MobileSentrixProduct | MobileSentrixDetailedProduct,
    ) -> dict[str, Any]:
        if isinstance(product, MobileSentrixDetailedProduct):
            if product.customer_price is None:
                raise ServicePricingValidationError(
                    "Selected Mobile Sentrix detailed product "
                    "does not contain customer_price."
                )

            if product.entity_id is None:
                raise ServicePricingValidationError(
                    "Selected Mobile Sentrix detailed product "
                    "does not contain entity_id."
                )

            if product.sku is None:
                raise ServicePricingValidationError(
                    "Selected Mobile Sentrix detailed product " "does not contain sku."
                )

            return {
                "supplier": product.supplier,
                "supplier_product_id": product.entity_id,
                "supplier_sku": product.sku,
                "part_name": product.name or "",
                "part_cost": product.customer_price,
                "supplier_in_stock": product.is_in_stock,
                "supplier_stock_qty": product.in_stock_qty,
            }

        if isinstance(product, MobileSentrixProduct):
            if product.unit_cost is None:
                raise ServicePricingValidationError(
                    "Selected Mobile Sentrix search product "
                    "does not contain unit_cost."
                )

            if product.supplier_product_id is None:
                raise ServicePricingValidationError(
                    "Selected Mobile Sentrix search product "
                    "does not contain supplier_product_id."
                )

            if product.supplier_sku is None:
                raise ServicePricingValidationError(
                    "Selected Mobile Sentrix search product "
                    "does not contain supplier_sku."
                )

            return {
                "supplier": product.supplier,
                "supplier_product_id": (product.supplier_product_id),
                "supplier_sku": product.supplier_sku,
                "part_name": product.name or "",
                "part_cost": product.unit_cost,
                "supplier_in_stock": product.in_stock,
                "supplier_stock_qty": None,
            }

        raise ServicePricingValidationError(
            "product must be a normalized Mobile Sentrix product."
        )
