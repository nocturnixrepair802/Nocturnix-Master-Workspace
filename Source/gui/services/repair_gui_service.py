class RepairGuiService:

    def __init__(self, application):

        self.application = application

        self.service = application.services.repairs

        self.customers = application.services.customers

        self.customer_devices = application.services.customer_devices

    # ======================================================
    # Search
    # ======================================================

    def search(self, text):

        return self.service.search(text)

    # ======================================================
    # Count
    # ======================================================

    def count(self):

        return self.service.count()

    # ======================================================
    # Customers
    # ======================================================

    def customers_list(self):

        return self.customers.all()

    # ======================================================
    # Devices
    # ======================================================


    def devices_list(self, customer_id=None):

        if customer_id is None:

            return self.customer_devices.all()

        return self.customer_devices.customer_devices(
            customer_id
        )
