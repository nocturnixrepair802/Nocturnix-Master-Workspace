from repositories.customer_repository import CustomerRepository
from repositories.device_repository import DeviceRepository
from repositories.inventory_repository import InventoryRepository
from repositories.manufacturer_repository import ManufacturerRepository
from repositories.service_repository import ServiceRepository
from repositories.supplier_repository import SupplierRepository
from repositories.compatibility_repository import CompatibilityRepository


class RepositoryManager:

    def __init__(self, database):

        self.database = database

        # ======================================================
        # Core Repositories
        # ======================================================

        self.customers = CustomerRepository(database)

        self.devices = DeviceRepository(database)

        self.inventory = InventoryRepository(database)

        self.manufacturers = ManufacturerRepository(database)

        self.services = ServiceRepository(database)

        self.suppliers = SupplierRepository(database)

        self.compatibility = CompatibilityRepository(database)

    # ======================================================
    # Utility
    # ======================================================

    def all(self):

        return {
            "customers": self.customers,
            "devices": self.devices,
            "inventory": self.inventory,
            "manufacturers": self.manufacturers,
            "services": self.services,
            "suppliers": self.suppliers,
            "compatibility": self.compatibility,
        }
