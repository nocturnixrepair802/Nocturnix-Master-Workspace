from repositories.repository_base import RepositoryBase


class ManufacturerRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "manufacturer_catalog")

    # ======================================================
    # Collections
    # ======================================================

    def all_manufacturers(self):

        return self.table.copy()

    def ids(self):

        return sorted(self.table["Manufacturer ID"].dropna().unique().tolist())

    def names(self):

        return sorted(self.table["Manufacturer"].dropna().unique().tolist())

    # ======================================================
    # Lookups
    # ======================================================

    def id_to_name(self, manufacturer_id):

        row = self.first("Manufacturer ID", manufacturer_id)

        if row is None:
            return manufacturer_id

        return row["Manufacturer"]

    def name_to_id(self, manufacturer):

        row = self.first("Manufacturer", manufacturer)

        if row is None:
            return None

        return row["Manufacturer ID"]

    def lookup(self):

        return dict(zip(self.table["Manufacturer ID"], self.table["Manufacturer"]))
