class CustomerDeviceService:

    def __init__(self, repository):

        self.repository = repository

    # ======================================================
    # Collections
    # ======================================================

    def all(self):

        return self.repository.all()

    def customer_devices(self, customer_id):

        return self.repository.customer_devices(customer_id)

    def get(self, device_id):

        return self.repository.get(device_id)

    def count(self):

        return self.repository.count()
