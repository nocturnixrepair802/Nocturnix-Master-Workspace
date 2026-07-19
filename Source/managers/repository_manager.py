from repositories.customer_repository import CustomerRepository
from repositories.device_repository import DeviceRepository
from repositories.manufacturer_repository import ManufacturerRepository
from repositories.service_repository import ServiceRepository
from repositories.compatibility_repository import CompatibilityRepository
from repositories.supplier_repository import SupplierRepository
from repositories.inventory_repository import InventoryRepository


class RepositoryManager:

    def __init__(self, database):

        self.customers = CustomerRepository(database)

        self.devices = DeviceRepository(database)

        self.manufacturers = ManufacturerRepository(database)

        self.services = ServiceRepository(database)

        self.compatibility = CompatibilityRepository(database)

        self.suppliers = SupplierRepository(database)

        self.inventory = InventoryRepository(database)