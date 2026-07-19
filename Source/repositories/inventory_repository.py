from repositories.repository_base import RepositoryBase
from models.inventory_item import InventoryItem


class InventoryRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(
            database,
            "parts_catalog"
        )

    def get(self, sku):

        row = self.first(
            "SKU",
            sku
        )

        if row is None:
            return None

        return InventoryItem(

            sku=row["SKU"],

            description=row["Description"],

            quantity=row["Quantity"],

            location=row["Location"]

        )

    def in_stock(self, sku):

        item = self.get(sku)

        if item is None:
            return False

        return item.quantity > 0