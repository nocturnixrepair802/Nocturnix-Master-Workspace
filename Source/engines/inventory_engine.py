from engines.engine_base import EngineBase


class InventoryEngine(EngineBase):

    def part_available(
        self,
        sku
    ):

        inventory = self.get_table(
            "parts_catalog"
        )

        match = inventory[
            inventory["SKU"] == sku
        ]

        if match.empty:

            return False

        quantity = int(
            match.iloc[0]["Quantity"]
        )

        return quantity > 0