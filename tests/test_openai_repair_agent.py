from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from nocturnix.openai_repair_agent import OpenAIRepairAgent


class FakeResponses:
    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.requests.append(kwargs)
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = FakeResponses(responses)


class FakeRepairService:
    def list_customers(self, owner_user_id: str, **kwargs: Any):
        return ([{"id": "cust_1", "owner_user_id": owner_user_id, "first_name": "Ada"}], 1)

    def create_customer(self, owner_user_id: str, request: Any):
        return {
            "id": "cust_created",
            "owner_user_id": owner_user_id,
            **request.model_dump(mode="json"),
        }


def function_call(name: str, arguments: dict[str, Any], call_id: str = "call_1") -> Any:
    return SimpleNamespace(
        type="function_call",
        name=name,
        arguments=json.dumps(arguments),
        call_id=call_id,
    )


def response(response_id: str, *, output: list[Any] | None = None, text: str = "") -> Any:
    return SimpleNamespace(id=response_id, output=output or [], output_text=text)


def test_agent_executes_read_tool_and_returns_final_text() -> None:
    client = FakeClient(
        [
            response(
                "resp_1",
                output=[function_call("search_customers", {"search": "Ada"})],
            ),
            response("resp_2", text="I found Ada's customer record."),
        ]
    )
    agent = OpenAIRepairAgent(client, FakeRepairService(), model="test-model")

    result = agent.run(owner_user_id="owner_1", message="Find Ada")

    assert result.text == "I found Ada's customer record."
    assert result.response_id == "resp_2"
    assert result.proposed_actions == []
    assert result.tool_results[0]["tool_name"] == "search_customers"
    assert len(client.responses.requests) == 2
    follow_up = client.responses.requests[1]
    assert follow_up["previous_response_id"] == "resp_1"
    assert follow_up["input"][0]["type"] == "function_call_output"
    assert json.loads(follow_up["input"][0]["output"])["total"] == 1


def test_agent_proposes_write_tool_without_executing() -> None:
    arguments = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.test",
        "phone": None,
        "company_name": None,
        "preferred_contact_method": "email",
        "notes": None,
        "status": "active",
    }
    client = FakeClient(
        [response("resp_1", output=[function_call("create_customer", arguments)])]
    )
    agent = OpenAIRepairAgent(client, FakeRepairService(), model="test-model")

    result = agent.run(owner_user_id="owner_1", message="Create Ada")

    assert result.response_id == "resp_1"
    assert result.tool_results == []
    assert len(result.proposed_actions) == 1
    assert result.proposed_actions[0].tool_name == "create_customer"
    assert "Please confirm" in result.text
    assert len(client.responses.requests) == 1


def test_agent_executes_exact_confirmed_write_action() -> None:
    arguments = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.test",
        "phone": None,
        "company_name": None,
        "preferred_contact_method": "email",
        "notes": None,
        "status": "active",
    }
    client = FakeClient(
        [
            response("resp_1", output=[function_call("create_customer", arguments)]),
            response("resp_2", text="Ada's customer record was created."),
        ]
    )
    agent = OpenAIRepairAgent(client, FakeRepairService(), model="test-model")
    key = agent.action_key("create_customer", arguments)

    result = agent.run(
        owner_user_id="owner_1",
        message="Yes, create it",
        confirmed_actions={key},
    )

    assert result.text == "Ada's customer record was created."
    assert result.tool_results[0]["result"]["id"] == "cust_created"
    assert result.tool_results[0]["result"]["owner_user_id"] == "owner_1"


def test_confirmation_is_bound_to_exact_arguments() -> None:
    approved = {"first_name": "Ada", "last_name": "Lovelace"}
    changed = {"first_name": "Grace", "last_name": "Hopper"}
    client = FakeClient(
        [response("resp_1", output=[function_call("create_customer", changed)])]
    )
    agent = OpenAIRepairAgent(client, FakeRepairService(), model="test-model")

    result = agent.run(
        owner_user_id="owner_1",
        message="Confirm",
        confirmed_actions={agent.action_key("create_customer", approved)},
    )

    assert len(result.proposed_actions) == 1
    assert result.proposed_actions[0].arguments == changed
    assert result.tool_results == []
