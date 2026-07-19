from managers.repository_manager import RepositoryManager

from engines.compatibility_engine import CompatibilityEngine
from engines.pricing_engine import PricingEngine
from engines.inventory_engine import InventoryEngine
from engines.quote_engine import QuoteEngine


class RepairManager:

    def __init__(self, database):

        self.repositories = RepositoryManager(database)

        self.compatibility = CompatibilityEngine(database)

        self.pricing = PricingEngine(database)

        self.inventory = InventoryEngine(database)

        self.quote = QuoteEngine(database)

    def customer(self, customer_id):

        return self.repositories.customers.get(customer_id)

    def device(self, device_id):

        return self.repositories.devices.get(device_id)

    def service(self, service_id):

        return self.repositories.services.get(service_id)

    def supplier(self, supplier_id):

        return self.repositories.suppliers.get(supplier_id)

    def part_available(self, sku):

        return self.inventory.part_available(sku)

    def calculate_price(

        self,

        labor_hours,

        parts_cost

    ):

        return self.pricing.calculate_price(

            labor_hours,

            parts_cost

        )

    def check_repair(

        self,

        device_family,

        service_id

    ):

        return self.compatibility.validate_repair(

            device_family,

            service_id

        )

    def create_quote(

        self,

        device_family,

        service_id,

        labor,

        parts

    ):

        return self.quote.generate_quote(

            device_family,

            service_id,

            labor,

            parts

        )