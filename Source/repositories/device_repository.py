from repositories.repository_base import RepositoryBase
from models.device import Device


class DeviceRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(
            database,
            "master_devices"
        )

    def get(self, device_id):

        row = self.first(
            "Device ID",
            device_id
        )

        if row is None:
            return None

        return Device(

            device_id=row["Device ID"],

            manufacturer=row["Manufacturer Code"],

            device_family=row["Device Family Code"],

            model=row["Device Model"],

            model_number=row["Model Number"],

            release_year=row["Release Year"],

            active=row["Active"]

        )

    def by_manufacturer(self, manufacturer_code):

        return self.filter(
            "Manufacturer Code",
            manufacturer_code
        )

    def by_family(self, family_code):

        return self.filter(
            "Device Family Code",
            family_code
        )