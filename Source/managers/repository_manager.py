from repositories.customer_device_repository import CustomerDeviceRepository
from repositories.customer_repository import CustomerRepository
from repositories.device_family_repository import DeviceFamilyRepository
from repositories.device_repository import DeviceRepository
from repositories.guide_repository import GuideRepository
from repositories.manufacturer_repository import ManufacturerRepository
from repositories.repair_repository import RepairRepository


class RepositoryManager:
    """
    Creates and owns all repository instances.
    """

    def __init__(self, database: dict):

        self.database = database

        # ==================================================
        # Customer Repositories
        # ==================================================

        self.customers = CustomerRepository(database)

        self.customer_devices = CustomerDeviceRepository(database)

        # ==================================================
        # Device Repositories
        # ==================================================

        self.devices = DeviceRepository(database)

        self.manufacturers = ManufacturerRepository(database)

        self.device_families = DeviceFamilyRepository(database)

        # ==================================================
        # Repair Repositories
        # ==================================================

        self.repairs = RepairRepository(database)

        # ==================================================
        # Technical Knowledge Repositories
        # ==================================================

        self.guides = GuideRepository(database)
