from repositories.repository_base import RepositoryBase


class ManufacturerRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "manufacturer_catalog")

    # ======================================================
    # Collections
    # ======================================================

    def all(self):

        return super().all()

    def ids(self):

        return sorted(self.table["Manufacturer ID"].dropna().unique().tolist())

    def names(self):

        return sorted(self.table["Manufacturer"].dropna().unique().tolist())

    # ======================================================
    # Lookups
    # ======================================================

    def id_to_name(self, manufacturer_id):

        row = self.first("Manufacturer ID", manufacturer_id)

        return manufacturer_id if row is None else row["Manufacturer"]

    def name_to_id(self, manufacturer):

        row = self.first("Manufacturer", manufacturer)

        return None if row is None else row["Manufacturer ID"]

    def lookup(self):

        return dict(zip(self.table["Manufacturer ID"], self.table["Manufacturer"]))
