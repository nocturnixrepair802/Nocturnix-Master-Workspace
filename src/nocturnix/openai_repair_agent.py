from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from nocturnix.repair_ai_tools import (
    REPAIR_TOOL_DEFINITIONS,
    RepairAssistantTools,
    RepairToolConfirmationRequired,
)


class ResponsesClient(Protocol):
    class Responses(Protocol):
        def create(self, **kwargs: Any) -> Any: ...

    responses: Responses


@dataclass(frozen=True)
class ProposedRepairAction:
    tool_name: str
    arguments: dict[str, Any]
    call_id: str


@dataclass
class RepairAgentResult:
    text: str
    response_id: str | None = None
    proposed_actions: list[ProposedRepairAction] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)


SYSTEM_INSTRUCTIONS = """
You are the Nocturnix repair operations assistant.
Use repair tools when the user asks about customers, devices, tickets, statuses, or notes.
Never invent IDs, ticket details, customer details, or tool results.
Read-only tools may be called immediately.
State-changing tools require explicit user confirmation before execution.
When information is missing, ask one concise question rather than guessing.
Keep customer data private and only use results returned for the authenticated user.
""".strip()


class OpenAIRepairAgent:
    """Runs a bounded Responses API function-calling loop for repair operations."""

    def __init__(
        self,
        client: ResponsesClient,
        repair_service: Any,
        *,
        model: str,
        max_tool_rounds: int = 6,
    ) -> None:
        self.client = client
        self.tools = RepairAssistantTools(repair_service)
        self.model = model
        self.max_tool_rounds = max_tool_rounds
        self._confirmation_required = {
            definition.name
            for definition in REPAIR_TOOL_DEFINITIONS
            if definition.requires_confirmation
        }

    def run(
        self,
        *,
        owner_user_id: str,
        message: str,
        previous_response_id: str | None = None,
        confirmed_actions: set[str] | None = None,
    ) -> RepairAgentResult:
        confirmed = confirmed_actions or set()
        request: dict[str, Any] = {
            "model": self.model,
            "instructions": SYSTEM_INSTRUCTIONS,
            "input": message,
            "tools": self.tools.openai_tools(),
            "tool_choice": "auto",
        }
        if previous_response_id:
            request["previous_response_id"] = previous_response_id

        response = self.client.responses.create(**request)
        tool_results: list[dict[str, Any]] = []

        for _round in range(self.max_tool_rounds):
            calls = self._function_calls(response)
            if not calls:
                return RepairAgentResult(
                    text=self._output_text(response),
                    response_id=getattr(response, "id", None),
                    tool_results=tool_results,
                )

            proposed: list[ProposedRepairAction] = []
            outputs: list[dict[str, Any]] = []
            for call in calls:
                name = str(call.name)
                call_id = str(call.call_id)
                arguments = self._arguments(call)
                action_key = self.action_key(name, arguments)

                if name in self._confirmation_required and action_key not in confirmed:
                    proposed.append(
                        ProposedRepairAction(
                            tool_name=name,
                            arguments=arguments,
                            call_id=call_id,
                        )
                    )
                    continue

                try:
                    result = self.tools.execute(
                        owner_user_id=owner_user_id,
                        tool_name=name,
                        arguments=arguments,
                        confirmed=action_key in confirmed,
                    )
                except RepairToolConfirmationRequired:
                    proposed.append(
                        ProposedRepairAction(
                            tool_name=name,
                            arguments=arguments,
                            call_id=call_id,
                        )
                    )
                    continue

                tool_results.append({"tool_name": name, "result": result})
                outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps(result, separators=(",", ":"), default=str),
                    }
                )

            if proposed:
                return RepairAgentResult(
                    text=self._confirmation_message(proposed),
                    response_id=getattr(response, "id", None),
                    proposed_actions=proposed,
                    tool_results=tool_results,
                )

            response = self.client.responses.create(
                model=self.model,
                instructions=SYSTEM_INSTRUCTIONS,
                previous_response_id=response.id,
                input=outputs,
                tools=self.tools.openai_tools(),
                tool_choice="auto",
            )

        raise RuntimeError("repair agent exceeded the maximum tool-call rounds")

    @staticmethod
    def action_key(tool_name: str, arguments: dict[str, Any]) -> str:
        canonical = json.dumps(arguments, sort_keys=True, separators=(",", ":"), default=str)
        return f"{tool_name}:{canonical}"

    @staticmethod
    def _function_calls(response: Any) -> list[Any]:
        return [
            item
            for item in (getattr(response, "output", None) or [])
            if getattr(item, "type", None) == "function_call"
        ]

    @staticmethod
    def _arguments(call: Any) -> dict[str, Any]:
        raw = getattr(call, "arguments", "{}")
        if isinstance(raw, dict):
            return raw
        parsed = json.loads(raw or "{}")
        if not isinstance(parsed, dict):
            raise ValueError("tool arguments must be a JSON object")
        return parsed

    @staticmethod
    def _output_text(response: Any) -> str:
        text = getattr(response, "output_text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()
        return "The repair request was processed, but the model returned no text response."

    @staticmethod
    def _confirmation_message(actions: list[ProposedRepairAction]) -> str:
        names = ", ".join(action.tool_name for action in actions)
        return f"Please confirm before I execute: {names}."


__all__ = [
    "OpenAIRepairAgent",
    "ProposedRepairAction",
    "RepairAgentResult",
    "ResponsesClient",
    "SYSTEM_INSTRUCTIONS",
]
