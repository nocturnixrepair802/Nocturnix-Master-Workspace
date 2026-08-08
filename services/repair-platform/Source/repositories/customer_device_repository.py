from repositories.repository_base import RepositoryBase


class CustomerDeviceRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "customer_devices")

    # ======================================================
    # Collections
    # ======================================================

    def all_devices(self):

        return self.table.copy()

    # ======================================================
    # Customer Devices
    # ======================================================

    def customer_devices(self, customer_id):

        return self.table[self.table["Customer ID"] == customer_id].copy()

    # ======================================================
    # Single Record
    # ======================================================

    def get(self, device_id):

        return self.first("Device ID", device_id)
