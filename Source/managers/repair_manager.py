from engines.quote_engine import QuoteEngine
from engines.pricing_engine import PricingEngine
from engines.inventory_engine import InventoryEngine
from engines.compatibility_engine import CompatibilityEngine


class RepairManager:

    def __init__(self, database):

        self.database = database

        # ======================================================
        # Business Engines
        # ======================================================

        self.quote = QuoteEngine(database)

        self.pricing = PricingEngine(database)

        self.inventory = InventoryEngine(database)

        self.compatibility = CompatibilityEngine(database)

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

    def validate_part(self, device, part):

        return self.compatibility.validate(device, part)
