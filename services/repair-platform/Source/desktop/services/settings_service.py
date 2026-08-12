from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DesktopSettings:
    square_environment: str = "sandbox"
    default_currency: str = "USD"
    default_created_by: str = "Ryan Brown"
    database_path: str = ""
    backup_limit: int = 10
    connection_mode: str = "auto"
    api_base_url: str = "http://127.0.0.1:8000"
    api_timeout_seconds: float = 2.0


class SettingsService:
    def __init__(
        self,
        settings_path: Path | None = None,
    ) -> None:
        self.settings_path = (
            settings_path
            if settings_path is not None
            else self._default_settings_path()
        )

    @staticmethod
    def _default_settings_path() -> Path:
        service_root = Path(__file__).resolve().parents[3]

        return service_root / "data" / "desktop_settings.local.json"

    def load(self) -> DesktopSettings:
        if not self.settings_path.exists():
            return DesktopSettings()

        try:
            raw = json.loads(
                self.settings_path.read_text(
                    encoding="utf-8",
                )
            )
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return DesktopSettings()

        if not isinstance(raw, dict):
            return DesktopSettings()

        return self._from_mapping(raw)

    def save(
        self,
        settings: DesktopSettings,
    ) -> DesktopSettings:
        normalized = self._normalize(settings)

        self.settings_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.settings_path.write_text(
            json.dumps(
                asdict(normalized),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return normalized

    def update(
        self,
        **values: Any,
    ) -> DesktopSettings:
        current = asdict(self.load())
        current.update(values)

        return self.save(self._from_mapping(current))

    @classmethod
    def _from_mapping(
        cls,
        values: dict[str, Any],
    ) -> DesktopSettings:
        defaults = DesktopSettings()

        return cls._normalize(
            DesktopSettings(
                square_environment=str(
                    values.get(
                        "square_environment",
                        defaults.square_environment,
                    )
                    or defaults.square_environment
                ),
                default_currency=str(
                    values.get(
                        "default_currency",
                        defaults.default_currency,
                    )
                    or defaults.default_currency
                ),
                default_created_by=str(
                    values.get(
                        "default_created_by",
                        defaults.default_created_by,
                    )
                    or defaults.default_created_by
                ),
                database_path=str(
                    values.get(
                        "database_path",
                        defaults.database_path,
                    )
                    or ""
                ),
                backup_limit=cls._coerce_backup_limit(
                    values.get(
                        "backup_limit",
                        defaults.backup_limit,
                    )
                ),
                connection_mode=str(
                    values.get(
                        "connection_mode",
                        defaults.connection_mode,
                    )
                    or defaults.connection_mode
                ),
                api_base_url=str(
                    values.get(
                        "api_base_url",
                        defaults.api_base_url,
                    )
                    or defaults.api_base_url
                ),
                api_timeout_seconds=cls._coerce_api_timeout(
                    values.get(
                        "api_timeout_seconds",
                        defaults.api_timeout_seconds,
                    )
                ),
            )
        )

    @classmethod
    def _normalize(
        cls,
        settings: DesktopSettings,
    ) -> DesktopSettings:
        environment = str(settings.square_environment).strip().lower()

        if environment not in {
            "sandbox",
            "production",
        }:
            environment = "sandbox"

        currency = str(settings.default_currency).strip().upper()

        if not currency:
            currency = "USD"

        created_by = str(settings.default_created_by).strip()

        if not created_by:
            created_by = "Ryan Brown"

        database_path = str(settings.database_path).strip()

        connection_mode = str(settings.connection_mode).strip().lower()

        if connection_mode not in {
            "offline",
            "online",
            "auto",
        }:
            connection_mode = "auto"

        api_base_url = str(settings.api_base_url).strip().rstrip("/")

        if not api_base_url:
            api_base_url = "http://127.0.0.1:8000"

        api_timeout_seconds = cls._coerce_api_timeout(settings.api_timeout_seconds)

        return DesktopSettings(
            square_environment=environment,
            default_currency=currency,
            default_created_by=created_by,
            database_path=database_path,
            backup_limit=cls._coerce_backup_limit(settings.backup_limit),
            connection_mode=connection_mode,
            api_base_url=api_base_url,
            api_timeout_seconds=api_timeout_seconds,
        )

    @staticmethod
    def _coerce_backup_limit(
        value: Any,
    ) -> int:
        try:
            result = int(value)
        except (
            TypeError,
            ValueError,
        ):
            return 10

        return max(
            result,
            1,
        )

    @staticmethod
    def _coerce_api_timeout(
        value: Any,
    ) -> float:
        try:
            result = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 2.0

        if result <= 0:
            return 2.0

        return result
