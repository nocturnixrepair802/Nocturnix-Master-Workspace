from repositories.repository_base import RepositoryBase


class SupplierRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "supplier_catalog")

    # ======================================================
    # Collections
    # ======================================================

    def all(self):

        return super().all()

    # ======================================================
    # Single Record
    # ======================================================

    def get(self, supplier_id):

        return self.first("Supplier ID", supplier_id)
