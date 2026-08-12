from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.request import urlopen

from desktop.services.settings_service import (
    DesktopSettings,
)


class ApiRequestError(RuntimeError):
    pass


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

    def _url(
        self,
        path: str,
    ) -> str:
        normalized_path = path.strip()

        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path

        return f"{self.base_url}" f"{normalized_path}"

    def get_json(
        self,
        path: str,
    ) -> Any:
        url = self._url(path)

        try:
            with urlopen(
                url,
                timeout=self.timeout_seconds,
            ) as response:
                raw = response.read()

            return json.loads(raw.decode("utf-8"))

        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ApiRequestError(f"API request failed: {url}: {exc}") from exc

    def health(
        self,
    ) -> ApiHealth:
        url = self._url("/health")

        try:
            payload = self.get_json("/health")
        except ApiRequestError as exc:
            return ApiHealth(
                available=False,
                status="unavailable",
                service="",
                url=url,
                error=str(exc),
            )

        if not isinstance(
            payload,
            dict,
        ):
            return ApiHealth(
                available=False,
                status="invalid",
                service="",
                url=url,
                error=("Health endpoint did not " "return an object."),
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

    def dashboard(
        self,
    ) -> dict[str, Any]:
        payload = self.get_json("/api/dashboard")

        if not isinstance(
            payload,
            dict,
        ):
            raise ApiRequestError("Dashboard endpoint did not " "return an object.")

        return dict(payload)

    def repair_queue(
        self,
    ) -> list[dict[str, Any]]:
        payload = self.get_json("/api/repair-queue")

        if not isinstance(
            payload,
            list,
        ):
            raise ApiRequestError("Repair queue endpoint did not " "return a list.")

        result: list[dict[str, Any]] = []

        for item in payload:
            if not isinstance(
                item,
                dict,
            ):
                raise ApiRequestError("Repair queue contained " "an invalid record.")

            result.append(dict(item))

        return result
