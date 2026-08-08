from __future__ import annotations

from typing import Any, Protocol


class AssistantToolProtocol(Protocol):
    def execute(
        self,
        input_data: dict[str, Any],
    ) -> dict[str, Any]: ...
