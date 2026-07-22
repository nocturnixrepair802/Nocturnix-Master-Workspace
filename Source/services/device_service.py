import pandas as pd
from core.base_service import BaseService


class DeviceService(BaseService):

    def __init__(self, repositories):

        super().__init__(repositories.devices)

        self.manufacturer_repository = repositories.manufacturers
        self.device_family_repository = repositories.device_families
        self.guide_repository = repositories.guides

    # ======================================================
    # READ
    # ======================================================

    def all(self) -> pd.DataFrame:

        return self.repository.all()

    def get(self, device_id) -> pd.Series | None:

        return self.repository.get(device_id)

    def count(self) -> int:

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

    def search(self, text: str = "") -> pd.DataFrame:

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

    def exists(self, device_name) -> bool:

        return self.repository.exists("Device ID", device_name)

    # ======================================================
    # Technical Knowledge
    # ======================================================

    def repair_guides(self, device_id):

        return self.guide_repository.by_device(device_id)

    def repair_count(self, device_id):

        return len(self.guide_repository.by_device(device_id))

    # ======================================================
    # Lookups
    # ======================================================

    def manufacturer_name(self, manufacturer_code):

        lookup = self.manufacturer_repository.lookup()

        return lookup.get(manufacturer_code, manufacturer_code)

    def family_name(self, family_code):

        lookup = self.device_family_repository.lookup()

        return lookup.get(family_code, family_code)
