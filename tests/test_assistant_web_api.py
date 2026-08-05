from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from nocturnix import create_app
from nocturnix.assistant.openai_provider import CodingProviderError
from nocturnix.config import Settings
from nocturnix.db import create_database_engine, create_session_factory
from nocturnix.persistence.models import (
    AssistantResultRow,
    AssistantTaskRow,
)


class FakeProvider:
    """Deterministic provider used by assistant API tests."""

    provider = "mock"
    model = "test-coding-model"

    def answer(
        self,
        message: str,
        context: str | None = None,
    ) -> str:
        return f"Typed answer for: {message}"


class FailingProvider:
    """Provider that raises a safe application-level error."""

    provider = "mock"
    model = "test-coding-model"

    def answer(
        self,
        message: str,
        context: str | None = None,
    ) -> str:
        raise CodingProviderError(
            "The AI provider is temporarily unavailable.",
            503,
        )


def make_test_settings(
    tmp_path: Path,
    **overrides: Any,
) -> Settings:
    """Build isolated test settings without loading the developer .env."""

    values: dict[str, Any] = {
        "database_url": f"sqlite:///{tmp_path / 'assistant.db'}",
        "database_migration_mode": "auto-test-only",
        "auth_mode": "development_header",
        "allow_development_header_auth": True,
        "coding_provider": "mock",
        "openai_enabled": False,
        "external_providers_enabled": False,
    }
    values.update(overrides)

    return Settings(
        **values,
    )


@pytest.fixture
def assistant_client(
    tmp_path: Path,
) -> Iterator[tuple[TestClient, str, FastAPI]]:
    """Create an isolated migrated application and test client."""

    settings = make_test_settings(tmp_path)
    app = create_app(settings)
    app.state.coding_provider = FakeProvider()

    with TestClient(app) as client:
        yield client, settings.database_url, app


def headers(
    user: str = "owner-one",
) -> dict[str, str]:
    """Return local development authentication headers."""

    return {
        "X-Nocturnix-Dev-User": user,
    }


def open_session(
    database_url: str,
) -> tuple[Engine, Session]:
    """Open a new SQLAlchemy session against the test database."""

    engine = create_database_engine(database_url)
    session = create_session_factory(engine)()

    return engine, session


def test_page_health_and_static_mount(
    assistant_client: tuple[TestClient, str, FastAPI],
) -> None:
    client, _, _ = assistant_client

    page = client.get("/assistant")

    assert page.status_code == 200
    assert "Development Assistant" in page.text

    static_response = client.get(
        "/static/coding-assistant.js",
    )

    assert static_response.status_code == 200

    health = client.get(
        "/api/assistant/health",
    )

    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "service": "nocturnix-development-assistant",
        "provider": "mock",
        "model": "test-coding-model",
        "openai_configured": False,
        "database_configured": True,
    }

    health_text = health.text.lower()

    assert "api_key" not in health_text
    assert "openai_api_key" not in health_text


def test_chat_validates_and_persists_completed_task(
    assistant_client: tuple[TestClient, str, FastAPI],
) -> None:
    client, database_url, _ = assistant_client

    invalid = client.post(
        "/api/assistant/chat",
        headers=headers(),
        json={
            "message": "   ",
        },
    )

    assert invalid.status_code == 422

    response = client.post(
        "/api/assistant/chat",
        headers=headers(),
        json={
            "message": "Explain FastAPI dependency injection.",
            "selected_files": [
                "app.py",
            ],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "completed"
    assert body["answer"].startswith(
        "Typed answer for:",
    )
    assert body["model"] == "test-coding-model"
    assert body["task_id"]
    assert body["result_id"]

    engine, session = open_session(database_url)

    try:
        task = session.scalar(
            select(AssistantTaskRow).where(
                AssistantTaskRow.id == body["task_id"],
            )
        )
        result = session.scalar(
            select(AssistantResultRow).where(
                AssistantResultRow.id == body["result_id"],
            )
        )

        assert task is not None
        assert task.owner_user_id == "owner-one"
        assert task.task_type == "coding_assistance"
        assert task.status == "completed"
        assert task.progress_percent == 100
        assert task.started_at is not None
        assert task.completed_at is not None

        assert result is not None
        assert result.owner_user_id == "owner-one"
        assert result.task_id == task.id
        assert result.result_type == "text"
        assert result.media_type == "text/markdown"
        assert result.content == {
            "text": body["answer"],
        }
    finally:
        session.close()
        engine.dispose()

    task_response = client.get(
        f"/api/assistant/tasks/{body['task_id']}",
        headers=headers(),
    )

    assert task_response.status_code == 200
    assert task_response.json()["id"] == body["task_id"]

    results_response = client.get(
        f"/api/assistant/tasks/{body['task_id']}/results",
        headers=headers(),
    )

    assert results_response.status_code == 200
    assert results_response.json()["items"][0]["content"] == {
        "text": body["answer"],
    }

    other_owner_task_response = client.get(
        f"/api/assistant/tasks/{body['task_id']}",
        headers=headers("owner-two"),
    )

    assert other_owner_task_response.status_code == 404

    other_owner_results_response = client.get(
        f"/api/assistant/tasks/{body['task_id']}/results",
        headers=headers("owner-two"),
    )

    assert other_owner_results_response.status_code == 404


def test_provider_failure_is_safe_and_marks_task_failed(
    assistant_client: tuple[TestClient, str, FastAPI],
) -> None:
    client, database_url, app = assistant_client

    app.state.coding_provider = FailingProvider()

    response = client.post(
        "/api/assistant/chat",
        headers=headers(),
        json={
            "message": "Review this code.",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == ("The AI provider is temporarily unavailable.")

    engine, session = open_session(database_url)

    try:
        task = session.scalar(
            select(AssistantTaskRow).order_by(
                AssistantTaskRow.created_at.desc(),
            )
        )

        assert task is not None
        assert task.owner_user_id == "owner-one"
        assert task.status == "failed"
        assert task.error_message == ("AI provider request failed safely.")
        assert task.completed_at is not None
    finally:
        session.close()
        engine.dispose()


def test_chat_requires_authentication_and_configuration(
    assistant_client: tuple[TestClient, str, FastAPI],
) -> None:
    client, _, app = assistant_client

    unauthenticated_response = client.post(
        "/api/assistant/chat",
        json={
            "message": "Hello",
        },
    )

    assert unauthenticated_response.status_code == 401

    app.state.coding_provider = None

    missing_provider_response = client.post(
        "/api/assistant/chat",
        headers=headers(),
        json={
            "message": "Hello",
        },
    )

    assert missing_provider_response.status_code == 503
    assert missing_provider_response.json()["detail"] == (
        "Coding provider is not configured."
    )


def test_application_selects_mock_provider(
    tmp_path: Path,
) -> None:
    app = create_app(
        make_test_settings(
            tmp_path,
            coding_provider="mock",
            openai_enabled=False,
            external_providers_enabled=False,
        )
    )

    provider = app.state.coding_provider

    assert provider is not None
    assert provider.provider == "mock"
    assert provider.model == "nocturnix-mock"


def test_application_selects_openai_provider(
    tmp_path: Path,
) -> None:
    app = create_app(
        make_test_settings(
            tmp_path,
            database_url=(f"sqlite:///{tmp_path / 'assistant-openai.db'}"),
            coding_provider="openai",
            openai_enabled=True,
            external_providers_enabled=True,
            openai_api_key="test-api-key",
            openai_model="test-openai-model",
        )
    )

    provider = app.state.coding_provider

    assert provider is not None
    assert provider.provider == "openai"
    assert provider.model == "test-openai-model"


def test_mock_application_chat_persists_task_and_result(
    tmp_path: Path,
) -> None:
    settings = make_test_settings(
        tmp_path,
        database_url=(f"sqlite:///{tmp_path / 'assistant-mock-chat.db'}"),
        coding_provider="mock",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post(
            "/api/assistant/chat",
            headers=headers(),
            json={
                "message": "Explain AssistantTaskService.",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "completed"
    assert body["model"] == "nocturnix-mock"
    assert "mock" in body["answer"].lower()

    engine, session = open_session(settings.database_url)

    try:
        task = session.scalar(
            select(AssistantTaskRow).where(
                AssistantTaskRow.id == body["task_id"],
            )
        )
        result = session.scalar(
            select(AssistantResultRow).where(
                AssistantResultRow.id == body["result_id"],
            )
        )

        assert task is not None
        assert task.status == "completed"

        assert result is not None
        assert result.task_id == task.id
        assert result.content == {
            "text": body["answer"],
        }
    finally:
        session.close()
        engine.dispose()
