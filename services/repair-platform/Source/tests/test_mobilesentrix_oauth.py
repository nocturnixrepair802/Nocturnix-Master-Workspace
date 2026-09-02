from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SOURCE_DIR = Path(__file__).resolve().parents[1]

if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SOURCE_DIR),
    )

from integrations.mobilesentrix.oauth import (
    MobileSentrixOAuthService,
)

MOBILESENTRIX_ENV_NAMES = (
    "MOBILESENTRIX_BASE_URL",
    "MOBILESENTRIX_CONSUMER_KEY",
    "MOBILESENTRIX_CONSUMER_SECRET",
    "MOBILESENTRIX_ACCESS_TOKEN",
    "MOBILESENTRIX_ACCESS_TOKEN_SECRET",
    "MOBILESENTRIX_CALLBACK_URL",
    "MOBILESENTRIX_PERSIST_TOKENS_TO_ENV_FILE",
)


@pytest.fixture(autouse=True)
def clean_mobilesentrix_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in MOBILESENTRIX_ENV_NAMES:
        monkeypatch.delenv(
            name,
            raising=False,
        )


def test_runtime_environment_overrides_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"

    env_path.write_text(
        (
            "MOBILESENTRIX_BASE_URL="
            "https://preprod.mobilesentrix.com\n"
            "MOBILESENTRIX_CONSUMER_KEY=file-key\n"
            "MOBILESENTRIX_CONSUMER_SECRET=file-secret\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_BASE_URL",
        "https://www.mobilesentrix.com",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_CONSUMER_KEY",
        "runtime-key",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_CONSUMER_SECRET",
        "runtime-secret",
    )

    service = MobileSentrixOAuthService(
        env_path=env_path,
    )

    assert service.base_url == ("https://www.mobilesentrix.com")

    assert service.consumer_key == ("runtime-key")

    assert service.consumer_secret == ("runtime-secret")


def test_process_only_mode_does_not_modify_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"

    original_text = "EXISTING_VALUE=unchanged\n"

    env_path.write_text(
        original_text,
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_PERSIST_TOKENS_TO_ENV_FILE",
        "false",
    )

    service = MobileSentrixOAuthService(
        env_path=env_path,
    )

    service._save_access_credentials(
        access_token="new-token",
        access_token_secret="new-secret",
    )

    assert os.environ["MOBILESENTRIX_ACCESS_TOKEN"] == "new-token"

    assert os.environ["MOBILESENTRIX_ACCESS_TOKEN_SECRET"] == "new-secret"

    assert env_path.read_text(encoding="utf-8") == original_text


def test_env_file_mode_persists_access_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"

    env_path.write_text(
        (
            "EXISTING_VALUE=unchanged\n"
            "MOBILESENTRIX_ACCESS_TOKEN=old-token\n"
            "MOBILESENTRIX_ACCESS_TOKEN_SECRET=old-secret\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_PERSIST_TOKENS_TO_ENV_FILE",
        "true",
    )

    service = MobileSentrixOAuthService(
        env_path=env_path,
    )

    service._save_access_credentials(
        access_token="new-token",
        access_token_secret="new-secret",
    )

    text = env_path.read_text(
        encoding="utf-8",
    )

    assert "EXISTING_VALUE=unchanged" in text

    assert "MOBILESENTRIX_ACCESS_TOKEN=new-token" in text

    assert "MOBILESENTRIX_ACCESS_TOKEN_SECRET=new-secret" in text

    assert "old-token" not in text

    assert "old-secret" not in text


def test_status_never_exposes_secret_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"

    env_path.write_text(
        "",
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_BASE_URL",
        "https://www.mobilesentrix.com",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_CONSUMER_KEY",
        "consumer-key-value",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_CONSUMER_SECRET",
        "consumer-secret-value",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_ACCESS_TOKEN",
        "access-token-value",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_ACCESS_TOKEN_SECRET",
        "access-token-secret-value",
    )

    service = MobileSentrixOAuthService(
        env_path=env_path,
    )

    status = service.status()

    serialized = repr(status)

    assert status["consumer_configured"] is True

    assert status["authorized"] is True

    assert "consumer-key-value" not in serialized

    assert "consumer-secret-value" not in serialized

    assert "access-token-value" not in serialized

    assert "access-token-secret-value" not in serialized


@pytest.mark.parametrize(
    (
        "configured_value",
        "expected",
    ),
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("off", False),
    ],
)
def test_token_persistence_boolean_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    configured_value: str,
    expected: bool,
) -> None:
    env_path = tmp_path / ".env"

    env_path.write_text(
        "",
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_PERSIST_TOKENS_TO_ENV_FILE",
        configured_value,
    )

    service = MobileSentrixOAuthService(
        env_path=env_path,
    )

    assert service.persist_tokens_to_env_file is expected


def test_invalid_token_persistence_value_uses_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"

    env_path.write_text(
        "",
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "MOBILESENTRIX_PERSIST_TOKENS_TO_ENV_FILE",
        "invalid-value",
    )

    service = MobileSentrixOAuthService(
        env_path=env_path,
    )

    assert service.persist_tokens_to_env_file is True
