from engines.compatibility_engine import CompatibilityEngine
from engines.pricing_engine import PricingEngine


class QuoteEngine:

    def __init__(self, database, compatibility: CompatibilityEngine):

        self.compatibility = compatibility

        self.pricing = PricingEngine(database)

    def generate(

        self,

        device_family,

        service_id,

        labor_hours,

        parts_cost

    ):

        supported = self.compatibility.validate(

            device_family,

            service_id

        )

        if not supported.supported:

            # TODO (Phase 2): Remove compatibility shim after canonical workbook migration.
            return {
                "supported": supported.supported,
                "reason": supported.reason,
                "requires_capability": supported.requires_capability,
            }

        pricing = self.pricing.calculate(
            labor_hours,
            parts_cost
        )

        return {

            "supported": True,

            "pricing": pricing

        }
