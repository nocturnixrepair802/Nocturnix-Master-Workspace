from __future__ import annotations

from typing import Any

from nocturnix.repair_services import RepairService


class RepairAssistantTool:
    def __init__(self, repair_service: RepairService) -> None:
        self._repair_service = repair_service

    def execute(
        self,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError
