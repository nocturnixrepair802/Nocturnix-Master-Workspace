from services.customer_service import CustomerService
from services.device_service import DeviceService
from services.repair_service import RepairService
from services.customer_device_service import CustomerDeviceService

class ServiceManager:

    def __init__(self, repositories):

        self.repositories = repositories

        # ======================================================
        # Core Services
        # ======================================================

        self.customers = CustomerService(
            repositories.customers
        )

        self.customer_devices = CustomerDeviceService(
            repositories.customer_devices
        )

        self.devices = DeviceService(
            repositories
        )

        self.repairs = RepairService(repositories.repairs)

    # ======================================================
    # Utility
    # ======================================================

    def all(self):

        return {
            "customers": self.customers,
            "devices": self.devices,
            "repairs": self.repairs,
        }
