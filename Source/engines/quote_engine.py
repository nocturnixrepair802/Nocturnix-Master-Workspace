from engines.compatibility_engine import CompatibilityEngine
from engines.pricing_engine import PricingEngine


class QuoteEngine:

    def __init__(self, database):

        self.compatibility = CompatibilityEngine(database)

        self.pricing = PricingEngine(database)

    def generate_quote(

        self,

        device_family,

        service_id,

        labor_hours,

        parts_cost

    ):

        supported = self.compatibility.validate_repair(

            device_family,

            service_id

        )

        if not supported["supported"]:

            return supported

        pricing = self.pricing.calculate_price(

            labor_hours,

            parts_cost

        )

        return {

            "supported": True,

            "pricing": pricing

        }