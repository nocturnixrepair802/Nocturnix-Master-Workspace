from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    supported: bool
    reason: str
    requires_capability: str | None = None


@dataclass(frozen=True, slots=True)
class InventoryAvailability:
    sku: str
    requested_quantity: int
    available_quantity: int
    sufficient: bool


@dataclass(frozen=True, slots=True)
class PricingResult:
    labor_cost: Decimal
    parts_cost: Decimal
    processing_fees: Decimal
    subtotal: Decimal
    retail: Decimal


@dataclass(frozen=True, slots=True)
class QuoteResult:
    supported: bool
    reason: str | None = None
    pricing: PricingResult | None = None
