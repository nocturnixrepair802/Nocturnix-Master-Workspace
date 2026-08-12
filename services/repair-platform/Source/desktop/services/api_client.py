from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.request import urlopen

from desktop.services.settings_service import (
    DesktopSettings,
)


@dataclass(frozen=True)
class ApiHealth:
    available: bool
    status: str
    service: str
    url: str
    error: str = ""


class ApiClient:
    def __init__(
        self,
        settings: DesktopSettings,
    ) -> None:
        self.settings = settings

        self.base_url = settings.api_base_url.strip().rstrip("/")

        self.timeout_seconds = settings.api_timeout_seconds

    def health(
        self,
    ) -> ApiHealth:
        url = f"{self.base_url}/health"

        try:
            with urlopen(
                url,
                timeout=self.timeout_seconds,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))

        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            return ApiHealth(
                available=False,
                status="unavailable",
                service="",
                url=url,
                error=str(exc),
            )

        status = str(
            payload.get(
                "status",
                "",
            )
        ).strip()

        service = str(
            payload.get(
                "service",
                "",
            )
        ).strip()

        return ApiHealth(
            available=(status.lower() == "ok"),
            status=status,
            service=service,
            url=url,
        )
