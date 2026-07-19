from repositories.repository_base import RepositoryBase
from models.supplier import Supplier


class SupplierRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(
            database,
            "supplier_catalog"
        )

    def get(self, supplier_id):

        row = self.first(
            "Supplier ID",
            supplier_id
        )

        if row is None:
            return None

        return Supplier(

            supplier_id=row["Supplier ID"],

            supplier=row["Supplier"],

            website=row["Website"],

            notes=row["Notes"]

        )

    def all_suppliers(self):

        suppliers = []

        for _, row in self.table.iterrows():

            suppliers.append(

                Supplier(

                    supplier_id=row["Supplier ID"],

                    supplier=row["Supplier"],

                    website=row["Website"],

                    notes=row["Notes"]

                )

            )

        return suppliers