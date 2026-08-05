from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from nocturnix import create_app
from nocturnix.config import Settings

OWNER_HEADERS = {"X-Nocturnix-Dev-User": "repair-owner-001"}


def base_settings(tmp_path: Path, **overrides):
    values: dict[str, Any] = {
        "database_url": f"sqlite:///{tmp_path / 'openai_config.db'}",
        "database_migration_mode": "auto-test-only",
        "auth_mode": "development_header",
        "allow_development_header_auth": True,
        "rate_limit_per_minute": 500,
    }
    values.update(overrides)
    return Settings(**values)


def test_openai_requires_external_provider_opt_in(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="EXTERNAL_PROVIDERS_ENABLED"):
        base_settings(
            tmp_path,
            openai_enabled=True,
            openai_api_key="test-key",
        )


def test_openai_requires_api_key(tmp_path: Path) -> None:
    with pytest.raises(
        ValidationError,
        match=r"openai_api_key|OPENAI_API_KEY",
    ):
        base_settings(
            tmp_path,
            external_providers_enabled=True,
            openai_enabled=True,
            openai_api_key=None,
        )


def test_external_providers_require_openai_provider(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="OPENAI_ENABLED"):
        base_settings(tmp_path, external_providers_enabled=True)


def test_repair_agent_endpoint_is_disabled_by_default(tmp_path: Path) -> None:
    app = create_app(base_settings(tmp_path))
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ai/repair-tools/chat",
            headers=OWNER_HEADERS,
            json={"message": "Find Ada Lovelace"},
        )
    assert response.status_code == 503
    assert response.json()["detail"] == "OpenAI repair agent is not enabled"


def test_openai_configuration_accepts_explicit_complete_opt_in(tmp_path: Path) -> None:
    settings = base_settings(
        tmp_path,
        external_providers_enabled=True,
        openai_enabled=True,
        openai_api_key="test-key",
        openai_model="gpt-test",
    )
    assert settings.openai_enabled is True
    assert settings.external_providers_enabled is True
    assert settings.openai_api_key == "test-key"
    assert settings.openai_model == "gpt-test"
