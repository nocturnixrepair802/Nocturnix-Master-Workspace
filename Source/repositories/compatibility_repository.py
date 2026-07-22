from repositories.repository_base import RepositoryBase


class CompatibilityRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "compatibility")

    # ======================================================
    # Collections
    # ======================================================

    def all(self):

        return super().all()

    # ======================================================
    # Single Record
    # ======================================================

    def get(self, compatibility_id):

        return self.first("Compatibility ID", compatibility_id)

    # ======================================================
    # Search
    # ======================================================

    def find_repair(self, device_family, service_id):

        return self.table[
            (self.table["Device Family"] == device_family)
            & (self.table["Service ID"] == service_id)
        ]

    def services_for_family(self, family_code):

        return self.filter("Device Family", family_code)

    def supported_services(self, family_code):

        df = self.services_for_family(family_code)

        return df[df["Supported"].fillna(False)]
