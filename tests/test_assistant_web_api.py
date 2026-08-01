from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Table, select

from nocturnix import create_app
from nocturnix.assistant.openai_provider import CodingProviderError
from nocturnix.config import Settings
from nocturnix.db import create_database_engine, create_session_factory
from nocturnix.persistence.models import AssistantResultRow, AssistantTaskRow


class FakeProvider:
    model = "test-coding-model"

    def answer(self, message: str, context: str | None = None) -> str:
        return f"Typed answer for: {message}"


class FailingProvider:
    model = "test-coding-model"

    def answer(self, message: str, context: str | None = None) -> str:
        raise CodingProviderError("The AI provider is temporarily unavailable.", 503)


@pytest.fixture
def assistant_client(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'assistant.db'}"

    app = create_app(
        Settings(
            database_url=database_url,
            database_migration_mode="auto-test-only",
            auth_mode="development_header",
            allow_development_header_auth=True,
        )
    )

    schema_engine = create_database_engine(database_url)

    assistant_task_table = cast(
        Table,
        AssistantTaskRow.__table__,
    )
    assistant_result_table = cast(
        Table,
        AssistantResultRow.__table__,
    )

    assistant_task_table.create(
        bind=schema_engine,
        checkfirst=True,
    )
    assistant_result_table.create(
        bind=schema_engine,
        checkfirst=True,
    )
    schema_engine.dispose()

    app.state.coding_provider = FakeProvider()

    with TestClient(app) as client:
        yield client, database_url


def headers(user: str = "owner-one") -> dict[str, str]:
    return {"X-Nocturnix-Dev-User": user}


def test_page_health_and_static_mount(assistant_client) -> None:
    client, _ = assistant_client
    page = client.get("/assistant")
    assert page.status_code == 200
    assert "Development Assistant" in page.text
    assert client.get("/static/coding-assistant.js").status_code == 200

    health = client.get("/api/assistant/health")
    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "service": "nocturnix-development-assistant",
        "openai_configured": False,
        "database_configured": True,
    }
    assert "api_key" not in health.text.lower()


def test_chat_validates_and_persists_completed_task(assistant_client) -> None:
    client, database_url = assistant_client
    invalid = client.post("/api/assistant/chat", headers=headers(), json={"message": "   "})
    assert invalid.status_code == 422

    response = client.post(
        "/api/assistant/chat",
        headers=headers(),
        json={"message": "Explain FastAPI dependency injection.", "selected_files": ["app.py"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["answer"].startswith("Typed answer")
    assert body["model"] == "test-coding-model"

    engine = create_database_engine(database_url)
    session = create_session_factory(engine)()
    try:
        task = session.scalar(
            select(AssistantTaskRow).where(AssistantTaskRow.id == body["task_id"])
        )
        result = session.scalar(
            select(AssistantResultRow).where(AssistantResultRow.id == body["result_id"])
        )
        assert task is not None and task.status == "completed" and task.started_at is not None
        assert result is not None and result.content == {"text": body["answer"]}
    finally:
        session.close()
        engine.dispose()

    task_response = client.get(f"/api/assistant/tasks/{body['task_id']}", headers=headers())
    assert task_response.status_code == 200
    results = client.get(f"/api/assistant/tasks/{body['task_id']}/results", headers=headers())
    assert results.status_code == 200
    assert results.json()["items"][0]["content"] == {"text": body["answer"]}
    assert (
        client.get(
            f"/api/assistant/tasks/{body['task_id']}", headers=headers("owner-two")
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/assistant/tasks/{body['task_id']}/results", headers=headers("owner-two")
        ).status_code
        == 404
    )


def test_provider_failure_is_safe_and_marks_task_failed(assistant_client) -> None:
    client, database_url = assistant_client
    client.app.state.coding_provider = FailingProvider()
    response = client.post(
        "/api/assistant/chat", headers=headers(), json={"message": "Review this code."}
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "The AI provider is temporarily unavailable."

    engine = create_database_engine(database_url)
    session = create_session_factory(engine)()
    try:
        task = session.scalar(select(AssistantTaskRow).order_by(AssistantTaskRow.created_at.desc()))
        assert task is not None
        assert task.status == "failed"
        assert task.error_message == "AI provider request failed safely."
    finally:
        session.close()
        engine.dispose()


def test_chat_requires_authentication_and_configuration(assistant_client) -> None:
    client, _ = assistant_client
    assert client.post("/api/assistant/chat", json={"message": "Hello"}).status_code == 401
    client.app.state.coding_provider = None
    response = client.post("/api/assistant/chat", headers=headers(), json={"message": "Hello"})
    assert response.status_code == 503
    assert response.json()["detail"] == "OpenAI is not configured."
