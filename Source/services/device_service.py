class DeviceService:

    def __init__(self, repositories):

        self.repository = repositories.devices

        self.repository = repositories.devices

        self.manufacturer_repository = repositories.manufacturers

        self.device_family_repository = repositories.device_families

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

        return self.manufacturer_repository.names()

    def families(self, manufacturer):

        return self.device_family_repository.names()

    def devices(self, manufacturer, family):

        return self.repository.devices(manufacturer, family)

    # ======================================================
    # Search
    # ======================================================

    def search(self, text):

        df = self.repository.search(text).copy()

        manufacturer_lookup = self.manufacturer_repository.lookup()

        family_lookup = self.device_family_repository.lookup()

        df["Manufacturer"] = df["Manufacturer Code"].map(manufacturer_lookup)

        df["Device Family"] = df["Device Family Code"].map(family_lookup)

        return df

    # ======================================================
    # Filtering
    # ======================================================

    def by_manufacturer(self, manufacturer):

        if manufacturer == "All Manufacturers":

            return self.search("")

        manufacturer_id = self.manufacturer_repository.name_to_id(
            manufacturer
        )

        df = self.repository.table.copy()

        df = df[
            df["Manufacturer Code"] == manufacturer_id
        ]

        manufacturer_lookup = self.manufacturer_repository.lookup()

        family_lookup = self.device_family_repository.lookup()

        df["Manufacturer"] = df["Manufacturer Code"].map(
            manufacturer_lookup
        )

        df["Device Family"] = df["Device Family Code"].map(
            family_lookup
        )

        return df

    # ======================================================
    # Validation
    # ======================================================

    def exists(self, device_name):

        return self.repository.exists("Device", device_name)
