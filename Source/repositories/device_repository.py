from repositories.repository_base import RepositoryBase
from models.device import Device


class DeviceRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "master_devices")
        print("\n===== MASTER DEVICES COLUMNS =====")
        print(self.table.columns.tolist())
        print("==================================\n")

    # ======================================================
    # Single Device
    # ======================================================

    def get(self, device_id):

        row = self.first("Device ID", device_id)

        if row is None:
            return None

        return Device(
            device_id=row.get("Device ID"),
            manufacturer=row.get("Manufacturer"),
            device_family=row.get("Device Family"),
            device_name=row.get("Device"),
            model_number=row.get("Model Number", ""),
            color=row.get("Color", ""),
            storage=row.get("Storage", ""),
            active=row.get("Active", True),
        )

    # ======================================================
    # Collections
    # ======================================================

    def all_devices(self):

        return self.table.copy()

    def manufacturers(self):

        return sorted(self.table["Manufacturer"].dropna().unique().tolist())

    def families(self, manufacturer):

        df = self.table

        return sorted(
            df[df["Manufacturer"] == manufacturer]["Device Family"]
            .dropna()
            .unique()
            .tolist()
        )

    def devices(self, manufacturer, family):

        df = self.table

        return sorted(
            df[(df["Manufacturer"] == manufacturer) & (df["Device Family"] == family)][
                "Device"
            ]
            .dropna()
            .unique()
            .tolist()
        )

    # ======================================================
    # Search
    # ======================================================

    def search(self, text):

        if not text:
            return self.table.copy()

        text = str(text).lower()

        mask = (
            self.table["Manufacturer"].fillna("").str.lower().str.contains(text)
            | self.table["Device"].fillna("").str.lower().str.contains(text)
            | self.table["Device Family"].fillna("").str.lower().str.contains(text)
        )

        return self.table[mask].copy()
