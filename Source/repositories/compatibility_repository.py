from repositories.repository_base import RepositoryBase
from models.compatibility import Compatibility


class CompatibilityRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(
            database,
            "compatibility"
        )

    def get(self, compatibility_id):

        row = self.first(
            "Compatibility ID",
            compatibility_id
        )

        if row is None:
            return None

        return Compatibility(

            compatibility_id=row["Compatibility ID"],

            device_family=row["Device Family"],

            service_id=row["Service ID"],

            supported=row["Supported"],

            required_capability=row["Requires Capability"],

            notes=row["Notes"]

        )

    def find_repair(

        self,

        device_family,

        service_id

    ):

        return self.table[

            (self.table["Device Family"] == device_family)

            &

            (self.table["Service ID"] == service_id)

        ]