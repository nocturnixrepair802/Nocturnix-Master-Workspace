import warnings

from engines.compatibility_engine import CompatibilityEngine
from engines.inventory_engine import InventoryEngine
from engines.pricing_engine import PricingEngine
from engines.quote_engine import QuoteEngine
from engines.results import CompatibilityResult
from repositories.compatibility_repository import CompatibilityRepository


class RepairManager:

    def __init__(self, database, repositories=None):

        self.database = database

        # ======================================================
        # Business Engines
        # ======================================================

        self.pricing = PricingEngine(database)

        self.inventory = InventoryEngine(database)

        compatibility_repository = (
            repositories.compatibility
            if repositories is not None
            else CompatibilityRepository(database)
        )
        self.compatibility = CompatibilityEngine(compatibility_repository)

        self.quote = QuoteEngine(database, self.compatibility)

    # ======================================================
    # Repair Quote
    # ======================================================

    def build_quote(
        self,
        device_family,
        service_id,
        labor_hours,
        parts_cost,
    ):

        return self.quote.generate(
            device_family=device_family,
            service_id=service_id,
            labor_hours=labor_hours,
            parts_cost=parts_cost,
        )

    # ======================================================
    # Pricing
    # ======================================================

    def calculate_price(self, service, parts=None):

        return self.pricing.calculate(service, parts or [])

    # ======================================================
    # Inventory
    # ======================================================

    def check_inventory(self, sku, quantity=1):

        return self.inventory.available(sku, quantity)

    # ======================================================
    # Compatibility
    # ======================================================

    def validate_service(
        self,
        device_family_code: str,
        service_id: str,
    ) -> CompatibilityResult:
        return self.compatibility.validate(device_family_code, service_id)

    def validate_part(self, device, part):
        # TODO (Phase 2): Remove compatibility shim after canonical workbook migration.

        warnings.warn(
            "validate_part() is deprecated; it validates service compatibility. "
            "Use validate_service().",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.validate_service(device, part)
