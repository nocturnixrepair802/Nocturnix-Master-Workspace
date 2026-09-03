from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ServicePricingRule:
    """
    Governed Nocturnix pricing and labor rule for a canonical
    Service Type.

    Percentage values are decimal fractions:

        12% -> Decimal("0.12")
        30% -> Decimal("0.30")
    """

    service_type_id: str
    service_type: str
    service_category_id: str


    default_labor_hours: Decimal
    labor_profile_id: str
    labor_tier: str
    hourly_rate: Decimal
    minimum_charge: Decimal

    target_margin: Decimal
    minimum_margin: Decimal

    overhead_rate: Decimal
    warranty_rate: Decimal
    risk_rate: Decimal
    processing_rate: Decimal

    rounding_rule: str = "End in .99"

    variant_key: str = "BASE"
    variant_name: str | None = None


@dataclass(frozen=True, slots=True)
class ServicePricingPreview:
    """
    Read-only assembled pricing preview.

    This model contains the identities and supplier information
    surrounding the pure PricingEngine calculation.
    """

    device_id: str
    device_model: str
    manufacturer_id: str
    manufacturer: str

    service_type_id: str
    service_type: str
    service_category_id: str

    supplier: str
    supplier_product_id: str
    supplier_sku: str
    part_name: str
    part_cost: Decimal

    supplier_in_stock: bool | None
    supplier_stock_qty: int | None

    default_labor_hours: Decimal
    labor_profile_id: str
    labor_tier: str
    hourly_rate: Decimal
    minimum_charge: Decimal

    calculated_labor_cost: Decimal
    billable_labor_cost: Decimal

    shipping: Decimal
    consumables: Decimal

    base_direct_cost: Decimal

    overhead_rate: Decimal
    overhead_reserve: Decimal

    warranty_rate: Decimal
    warranty_reserve: Decimal

    risk_rate: Decimal
    risk_reserve: Decimal

    processing_rate: Decimal
    processing_reserve: Decimal

    total_internal_cost: Decimal

    target_margin: Decimal
    minimum_margin: Decimal

    raw_retail_price: Decimal
    recommended_retail_price: Decimal

    gross_profit: Decimal
    gross_margin: Decimal

    pricing_status: str

    market_low: Decimal | None = None
    market_average: Decimal | None = None
    market_high: Decimal | None = None
    market_sample_count: int | None = None
    market_position: str | None = None

