from repositories.customer_repository import CustomerRepository
from repositories.device_repository import DeviceRepository
from repositories.manufacturer_repository import ManufacturerRepository
from repositories.device_family_repository import DeviceFamilyRepository


class RepositoryManager:

    def __init__(self, database):

        self.database = database

        # ==================================================
        # Customer Repositories
        # ==================================================

        self.customers = CustomerRepository(database)

        # ==================================================
        # Device Repositories
        # ==================================================

        self.devices = DeviceRepository(database)

        self.manufacturers = ManufacturerRepository(database)

        self.device_families = DeviceFamilyRepository(database)
