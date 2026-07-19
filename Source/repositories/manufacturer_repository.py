from repositories.repository_base import RepositoryBase
from models.manufacturer import Manufacturer


class ManufacturerRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(
            database,
            "manufacturer_catalog"
        )

    def get(self, manufacturer_id):

        row = self.first(
            "Manufacturer ID",
            manufacturer_id
        )

        if row is None:
            return None

        return Manufacturer(

            manufacturer_id=row["Manufacturer ID"],

            manufacturer=row["Manufacturer"],

            website=row["Website"],

            active=row["Active"]

        )

    def all_manufacturers(self):

        manufacturers = []

        for _, row in self.table.iterrows():

            manufacturers.append(

                Manufacturer(

                    manufacturer_id=row["Manufacturer ID"],

                    manufacturer=row["Manufacturer"],

                    website=row["Website"],

                    active=row["Active"]

                )

            )

        return manufacturers