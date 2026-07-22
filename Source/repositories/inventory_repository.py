from repositories.repository_base import RepositoryBase


class InventoryRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "parts_catalog")

    def all(self):

        return super().all()

    def get(self, sku):

        return self.first("SKU", sku)

    def in_stock(self, sku):

        item = self.get(sku)

        if item is None:
            return False

        return int(item["Quantity"]) > 0
