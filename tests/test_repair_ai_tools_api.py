from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings

OWNER_HEADERS = {"X-Nocturnix-Dev-User": "repair-ai-owner-001"}
OTHER_HEADERS = {"X-Nocturnix-Dev-User": "repair-ai-owner-002"}


@pytest.fixture
def repair_ai_client(tmp_path: Path):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path / 'repair_ai_tools.db'}",
            database_migration_mode="auto-test-only",
            auth_mode="development_header",
            allow_development_header_auth=True,
            rate_limit_per_minute=500,
        )
    )
    with TestClient(app) as client:
        yield client
    cast(Any, app).state.container.engine.dispose()


def execute_tool(
    client: TestClient,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    headers: dict[str, str] = OWNER_HEADERS,
    confirmed: bool = False,
):
    return client.post(
        "/api/v1/ai/repair-tools/execute",
        headers=headers,
        json={
            "tool_name": tool_name,
            "arguments": arguments,
            "confirmed": confirmed,
        },
    )


def test_repair_ai_tool_catalog_requires_authentication(repair_ai_client: TestClient) -> None:
    assert repair_ai_client.get("/api/v1/ai/repair-tools").status_code == 401

    response = repair_ai_client.get(
        "/api/v1/ai/repair-tools",
        headers=OWNER_HEADERS,
    )
    assert response.status_code == 200
    tools = {item["name"]: item for item in response.json()}
    assert "search_customers" in tools
    assert "create_customer" in tools
    assert tools["create_customer"]["type"] == "function"
    assert tools["create_customer"]["strict"] is True
    assert "parameters" in tools["create_customer"]


def test_repair_ai_tool_confirmation_and_execution(repair_ai_client: TestClient) -> None:
    arguments = {
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": "grace@example.test",
        "phone": "802-555-0110",
        "preferred_contact_method": "email",
        "notes": "Created through guarded AI tool execution",
    }

    blocked = execute_tool(repair_ai_client, "create_customer", arguments)
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "repair_tool_confirmation_required"

    created = execute_tool(
        repair_ai_client,
        "create_customer",
        arguments,
        confirmed=True,
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["tool_name"] == "create_customer"
    assert body["confirmed"] is True
    assert body["result"]["first_name"] == "Grace"
    customer_id = body["result"]["id"]

    searched = execute_tool(
        repair_ai_client,
        "search_customers",
        {"search": "hopper", "offset": 0, "limit": 20},
    )
    assert searched.status_code == 200, searched.text
    search_result = searched.json()["result"]
    assert search_result["total"] == 1
    assert search_result["items"][0]["id"] == customer_id

    retrieved = execute_tool(
        repair_ai_client,
        "get_customer",
        {"customer_id": customer_id},
    )
    assert retrieved.status_code == 200
    assert retrieved.json()["result"]["email"] == "grace@example.test"


def test_repair_ai_tool_unknown_name_and_owner_isolation(repair_ai_client: TestClient) -> None:
    unknown = execute_tool(repair_ai_client, "delete_everything", {})
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "repair_tool_not_found"

    created = execute_tool(
        repair_ai_client,
        "create_customer",
        {
            "first_name": "Katherine",
            "last_name": "Johnson",
            "email": "katherine@example.test",
            "preferred_contact_method": "email",
        },
        confirmed=True,
    )
    assert created.status_code == 200
    customer_id = created.json()["result"]["id"]

    hidden = execute_tool(
        repair_ai_client,
        "get_customer",
        {"customer_id": customer_id},
        headers=OTHER_HEADERS,
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "repair_not_found"
