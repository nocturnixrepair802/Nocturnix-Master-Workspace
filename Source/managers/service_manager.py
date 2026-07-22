from managers.repository_manager import RepositoryManager
from services.customer_device_service import CustomerDeviceService
from services.customer_service import CustomerService
from services.device_service import DeviceService
from services.repair_service import RepairService
from services.technical_knowledge_service import TechnicalKnowledgeService


class ServiceManager:
    """
    Creates and owns all business services.
    """

    def __init__(self, repositories: RepositoryManager):

        self.repositories = repositories

        self.repositories: RepositoryManager = repositories

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
        # Technical Knowledge Services
        # ======================================================

        self.technical = TechnicalKnowledgeService(repositories)

    # ======================================================
    # Utility
    # ======================================================

    def all(self) -> dict:

        return {
            "customers": self.customers,
            "customer_devices": self.customer_devices,
            "devices": self.devices,
            "repairs": self.repairs,
            "technical": self.technical,
        }
