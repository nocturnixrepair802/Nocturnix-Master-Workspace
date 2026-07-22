import math

from engines.results import CompatibilityResult
from repositories.compatibility_repository import CompatibilityRepository


class CompatibilityValueError(ValueError):
    """A compatibility row contains an invalid decision value."""


class CompatibilityEngine:

    NO_MATCH_REASON = "Repair not supported."

    def __init__(self, repository: CompatibilityRepository):
        self.repository = repository

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if value is None or type(value).__name__ == "NAType":
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        text = str(value).strip()
        return text or None

    def validate(
        self,
        device_family_code: str,
        service_id: str,
    ) -> CompatibilityResult:
        match = self.repository.find_service(device_family_code, service_id)

        if match is None:
            return CompatibilityResult(False, self.NO_MATCH_REASON)

        supported = match["Supported"]
        supported_type = type(supported)
        is_boolean = supported_type is bool or (
            supported_type.__module__ == "numpy" and supported_type.__name__ == "bool"
        )
        if not is_boolean:
            raise CompatibilityValueError(
                "Compatibility 'Supported' must be a non-null boolean for "
                f"device family '{device_family_code}' and service '{service_id}'."
            )
        normalized_supported = bool(supported)

        notes = match.get("Notes")
        reason = self._optional_text(notes) or (
            "Supported" if normalized_supported else self.NO_MATCH_REASON
        )
        capability = match.get("Requires Capability")
        requires_capability = self._optional_text(capability)

        return CompatibilityResult(normalized_supported, reason, requires_capability)
