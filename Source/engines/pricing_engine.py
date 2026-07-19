from engines.engine_base import EngineBase


class PricingEngine(EngineBase):

    def calculate_price(
        self,
        labor_hours,
        parts_cost
    ):

        labor = self.get_table("labor_rates")

        retail = self.get_table("retail_pricing")

        hourly_rate = float(
            labor.iloc[0]["Hourly Rate"]
        )

        labor_cost = labor_hours * hourly_rate

        markup = float(
            retail.iloc[0]["Markup"]
        )

        subtotal = labor_cost + parts_cost

        total = subtotal * markup

        return {

            "labor_cost": labor_cost,

            "parts_cost": parts_cost,

            "subtotal": subtotal,

            "retail": round(total, 2)

        }