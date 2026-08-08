from __future__ import annotations

from typing import Any, Protocol

from nocturnix.assistant.exceptions import AssistantToolNotFoundError
from nocturnix.assistant.models import AssistantTool


class AssistantToolHandler(Protocol):
    def __call__(self, input_data: dict[str, Any]) -> dict[str, Any]: ...


class AssistantToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[AssistantTool, AssistantToolHandler] = {}

    def register(
        self,
        tool: AssistantTool,
        handler: AssistantToolHandler,
    ) -> None:
        self._tools[tool] = handler

    def get(self, tool: AssistantTool) -> AssistantToolHandler:
        try:
            return self._tools[tool]
        except KeyError as exc:
            raise AssistantToolNotFoundError(
                f"Assistant tool is not registered: {tool.value}"
            ) from exc
