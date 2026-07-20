from repositories.repository_base import RepositoryBase


class DeviceRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "master_devices")

    # ======================================================
    # Collections
    # ======================================================

    def all_devices(self):

        return self.table.copy()

    # ======================================================
    # Search
    # ======================================================

    def search(self, text=""):

        if not text:
            return self.table.copy()

        text = str(text).lower()

        mask = (
            self.table["Device Model"].fillna("").str.lower().str.contains(text)
            | self.table["Model Number"].fillna("").str.lower().str.contains(text)
            | self.table["Manufacturer Code"].fillna("").str.lower().str.contains(text)
            | self.table["Device Family Code"].fillna("").str.lower().str.contains(text)
        )

        return self.table.loc[mask].copy()

    # ======================================================
    # Filters
    # ======================================================

    def manufacturers(self):

        return sorted(self.table["Manufacturer Code"].dropna().unique().tolist())

    def families(self, manufacturer_code):

        df = self.table[self.table["Manufacturer Code"] == manufacturer_code]

        return sorted(df["Device Family Code"].dropna().unique().tolist())

    def devices(self, manufacturer_code, family_code):

        df = self.table[
            (self.table["Manufacturer Code"] == manufacturer_code)
            & (self.table["Device Family Code"] == family_code)
        ]

        return sorted(df["Device Model"].dropna().unique().tolist())

    # ======================================================
    # Single Record
    # ======================================================

    def get(self, device_id):

        row = self.first("Device ID", device_id)

        if row is None:
            return None

        return row
