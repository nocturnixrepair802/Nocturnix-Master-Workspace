class RepairGuiService:

    def __init__(self, application):

        self.application = application

        self.service = application.services.repairs

        self.customers = application.services.customers

        self.customer_devices = application.services.customer_devices

        self.devices = application.services.devices

        self.compatibility = application.repositories.compatibility

        self.master_services = application.database["master_services"]

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

    # ======================================================
    # Customer Device
    # ======================================================

    def customer_device(self, device_id):

        return self.customer_devices.get(device_id)

    # ======================================================
    # Compatible Services
    # ======================================================


    def compatible_services(self, device_id):

        device = self.devices.get(device_id)

        if device is None:

            return []

        family = device["Device Family Code"]

        compatibility = self.compatibility.supported_services(family)

        if compatibility.empty:

            return []

        services = []

        for _, row in compatibility.iterrows():

            service_id = row["Service ID"]

            match = self.master_services[self.master_services["Service ID"] == service_id]

            if not match.empty:

                services.append(match.iloc[0]["Service Name"])

        return sorted(set(services))
