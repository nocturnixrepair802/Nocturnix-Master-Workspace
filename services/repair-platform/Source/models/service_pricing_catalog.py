from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ServicePricingCatalogRecord:
    """
    Persisted Nocturnix service-pricing snapshot.

    A catalog record combines:

    - a canonical Nocturnix device;
    - a governed Service Type and variant;
    - a selected supplier product;
    - the governed pricing-rule snapshot;
    - the resulting calculated price snapshot.

    Supplier observations and calculated values are snapshots.
    They do not replace Mobile Sentrix or PricingRuleProvider as
    their respective sources of truth.
    """

    pricing_record_id: str

    catalog_device_id: str

    service_type_id: str
    service_type: str
    service_category_id: str

    variant_key: str
    variant_name: str | None

    supplier: str
    supplier_product_id: str
    supplier_sku: str
    part_name: str

    quality_class: str | None
    quality_rank: int | None
    customer_facing_tier: str | None
    commercial_selection_status: str | None
    recommended_action: str | None

    part_cost: Decimal

    supplier_in_stock: bool | None
    supplier_stock_qty: int | None
    supplier_observed_at: datetime | None

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

    rounding_rule: str

    billable_labor_cost: Decimal
    shipping: Decimal
    consumables: Decimal

    base_direct_cost: Decimal
    total_internal_cost: Decimal

    recommended_price: Decimal

    gross_profit: Decimal
    gross_margin: Decimal

    pricing_status: str

    approved_price: Decimal | None
    approval_status: str
    approved_at: datetime | None
    approved_by: str | None

    created_at: datetime
    updated_at: datetime
