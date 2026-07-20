from repositories.repository_base import RepositoryBase


class DeviceFamilyRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "device_catalog")

    # ======================================================
    # Collections
    # ======================================================

    def all_families(self):

        return self.table.copy()

    def codes(self):

        return sorted(self.table["Device Family Code"].dropna().unique().tolist())

    def names(self):

        return sorted(self.table["Device Family"].dropna().unique().tolist())

    # ======================================================
    # Lookups
    # ======================================================

    def code_to_name(self, code):

        row = self.first("Device Family Code", code)

        if row is None:
            return code

        return row["Device Family"]

    def name_to_code(self, family):

        row = self.first("Device Family", family)

        if row is None:
            return None

        return row["Device Family Code"]

    def lookup(self):

        return dict(zip(self.table["Device Family Code"], self.table["Device Family"]))
