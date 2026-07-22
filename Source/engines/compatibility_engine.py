from engines.engine_base import EngineBase


class CompatibilityEngine(EngineBase):

    def validate(
        self,
        device_family,
        service_id
    ):

        compatibility = self.get_table(
            "compatibility"
        )

        match = compatibility[
            (compatibility["Device Family"] == device_family)
            &
            (compatibility["Service ID"] == service_id)
        ]

        if match.empty:

            return {
                "supported": False,
                "reason": "Repair not supported."
            }

        return {
            "supported": True,
            "reason": "Supported"
        }