from engines.engine_base import EngineBase


class InventoryEngine(EngineBase):

    def available(
        self,
        sku,
        requested_quantity=1
    ):

        inventory = self.get_table(
            "parts_catalog"
        )

        match = inventory[
            inventory["SKU"] == sku
        ]

        if match.empty:

            return False

        stock = int(match.iloc[0]["Quantity"])

        return stock >= requested_quantity
