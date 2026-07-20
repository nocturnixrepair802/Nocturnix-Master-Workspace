class DeviceService:

    def __init__(self, repository):

        self.repository = repository

    # ======================================================
    # READ
    # ======================================================

    def all(self):

        return self.repository.all_devices()

    def get(self, device_id):

        return self.repository.get(device_id)

    def count(self):

        return len(self.repository.table)

    # ======================================================
    # Catalog
    # ======================================================

    def manufacturers(self):

        return self.repository.manufacturers()

    def families(self, manufacturer):

        return self.repository.families(manufacturer)

    def devices(self, manufacturer, family):

        return self.repository.devices(manufacturer, family)

    # ======================================================
    # Search
    # ======================================================

    def search(self, text):

        return self.repository.search(text)

    # ======================================================
    # Filtering
    # ======================================================

    def by_manufacturer(self, manufacturer):

        return self.repository.filter("Manufacturer", manufacturer)

    def by_family(self, family):

        return self.repository.filter("Device Family", family)

    # ======================================================
    # Validation
    # ======================================================

    def exists(self, device_name):

        return self.repository.exists("Device", device_name)
