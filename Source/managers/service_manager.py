from services.customer_service import CustomerService
from services.device_service import DeviceService
from services.repair_service import RepairService
from services.supplier_service import SupplierService


class ServiceManager:

    def __init__(self, repositories):

        self.customers = CustomerService(
            repositories.customers
        )

        self.devices = DeviceService(
            repositories.devices
        )

        self.repairs = RepairService(
            repositories.services
        )

        self.suppliers = SupplierService(
            repositories.suppliers
        )