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
        )
    )

    settings = service.load()

    assert settings.square_environment == "production"
    assert settings.default_currency == "USD"
    assert settings.default_created_by == "Test User"
    assert settings.database_path == (r"D:\Data\operations.sqlite3")
    assert settings.backup_limit == 15


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
            "backup_limit": 0
        }
        """,
        encoding="utf-8",
    )

    settings = service.load()

    assert settings.square_environment == "sandbox"
    assert settings.default_currency == "USD"
    assert settings.default_created_by == "Ryan Brown"
    assert settings.backup_limit == 1


def test_update_preserves_existing_values(
    tmp_path: Path,
) -> None:
    service = SettingsService(tmp_path / "settings.json")

    service.save(
        DesktopSettings(
            square_environment="sandbox",
            default_currency="USD",
            default_created_by="Ryan Brown",
            backup_limit=10,
        )
    )

    updated = service.update(
        default_created_by="Alex Technician",
    )

    assert updated.square_environment == "sandbox"
    assert updated.default_currency == "USD"
    assert updated.default_created_by == ("Alex Technician")
    assert updated.backup_limit == 10
