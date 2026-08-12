from __future__ import annotations

from pathlib import Path

from desktop.services.settings_service import (
    DesktopSettings,
    SettingsService,
)


def test_load_returns_defaults_when_file_missing(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    settings = service.load()

    assert settings.square_environment == "sandbox"
    assert settings.default_currency == "USD"
    assert settings.default_created_by == "Ryan Brown"
    assert settings.database_path == ""
    assert settings.backup_limit == 10

    assert settings.connection_mode == "auto"
    assert settings.api_base_url == "http://127.0.0.1:8000"
    assert settings.api_timeout_seconds == 2.0


def test_save_and_load_round_trip(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    service.save(
        DesktopSettings(
            square_environment="production",
            default_currency="usd",
            default_created_by="Test User",
            database_path=r"D:\Data\operations.sqlite3",
            backup_limit=15,
            connection_mode="online",
            api_base_url="https://api.example.com/",
            api_timeout_seconds=5.5,
        )
    )

    settings = service.load()

    assert settings.square_environment == "production"
    assert settings.default_currency == "USD"
    assert settings.default_created_by == "Test User"
    assert settings.database_path == (r"D:\Data\operations.sqlite3")
    assert settings.backup_limit == 15

    assert settings.connection_mode == "online"
    assert settings.api_base_url == "https://api.example.com"
    assert settings.api_timeout_seconds == 5.5


def test_invalid_values_fall_back_safely(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    service.settings_path.write_text(
        """
        {
            "square_environment": "invalid",
            "default_currency": "",
            "default_created_by": "",
            "backup_limit": 0,
            "connection_mode": "invalid",
            "api_base_url": "",
            "api_timeout_seconds": 0
        }
        """,
        encoding="utf-8",
    )

    settings = service.load()

    assert settings.square_environment == "sandbox"
    assert settings.default_currency == "USD"
    assert settings.default_created_by == "Ryan Brown"
    assert settings.backup_limit == 1

    assert settings.connection_mode == "auto"
    assert settings.api_base_url == "http://127.0.0.1:8000"
    assert settings.api_timeout_seconds == 2.0


def test_update_preserves_existing_values(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    service.save(
        DesktopSettings(
            square_environment="sandbox",
            default_currency="USD",
            default_created_by="Ryan Brown",
            database_path="",
            backup_limit=10,
            connection_mode="auto",
            api_base_url="http://127.0.0.1:8000",
            api_timeout_seconds=2.0,
        )
    )

    updated = service.update(
        default_created_by="Alex Technician",
    )

    assert updated.square_environment == "sandbox"
    assert updated.default_currency == "USD"
    assert updated.default_created_by == ("Alex Technician")
    assert updated.database_path == ""
    assert updated.backup_limit == 10

    assert updated.connection_mode == "auto"
    assert updated.api_base_url == "http://127.0.0.1:8000"
    assert updated.api_timeout_seconds == 2.0


def test_connectivity_settings_round_trip(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    service.save(
        DesktopSettings(
            connection_mode="online",
            api_base_url="https://api.example.com/",
            api_timeout_seconds=5.5,
        )
    )

    settings = service.load()

    assert settings.connection_mode == "online"
    assert settings.api_base_url == "https://api.example.com"
    assert settings.api_timeout_seconds == 5.5


def test_invalid_connection_mode_falls_back_to_auto(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    service.settings_path.write_text(
        """
        {
            "connection_mode": "invalid"
        }
        """,
        encoding="utf-8",
    )

    settings = service.load()

    assert settings.connection_mode == "auto"


def test_invalid_api_settings_fall_back_safely(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    service.settings_path.write_text(
        """
        {
            "api_base_url": "",
            "api_timeout_seconds": 0
        }
        """,
        encoding="utf-8",
    )

    settings = service.load()

    assert settings.api_base_url == "http://127.0.0.1:8000"
    assert settings.api_timeout_seconds == 2.0


def test_connection_mode_is_normalized_to_lowercase(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    saved = service.save(
        DesktopSettings(
            connection_mode="ONLINE",
        )
    )

    assert saved.connection_mode == "online"


def test_api_timeout_accepts_numeric_string(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    service.settings_path.write_text(
        """
        {
            "api_timeout_seconds": "4.25"
        }
        """,
        encoding="utf-8",
    )

    settings = service.load()

    assert settings.api_timeout_seconds == 4.25


def test_api_timeout_invalid_text_falls_back(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    service.settings_path.write_text(
        """
        {
            "api_timeout_seconds": "invalid"
        }
        """,
        encoding="utf-8",
    )

    settings = service.load()

    assert settings.api_timeout_seconds == 2.0
