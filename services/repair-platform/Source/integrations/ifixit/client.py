from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

from integrations.ifixit.models import IFixitDeviceResult, IFixitGuideMetadata


class IFixitApiError(RuntimeError):
    """Raised when a public iFixit API request cannot be completed safely."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        timed_out: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.timed_out = timed_out


class IFixitClient:
    """Read-only client for metadata from the public iFixit API v2.0."""

    DEFAULT_BASE_URL = "https://www.ifixit.com/api/2.0"
    DEFAULT_TIMEOUT_SECONDS = 10.0
    USER_AGENT = "Nocturnix-Repair-Platform/0.7 (iFixit metadata integration)"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        normalized_base_url = base_url.strip().rstrip("/")
        parsed_url = urlsplit(normalized_base_url)

        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("iFixit base_url must be an absolute HTTP(S) URL.")

        if parsed_url.query or parsed_url.fragment:
            raise ValueError("iFixit base_url cannot contain a query or fragment.")

        if timeout_seconds <= 0:
            raise ValueError("iFixit timeout_seconds must be greater than zero.")

        self.base_url = normalized_base_url
        self.timeout_seconds = timeout_seconds

    def search_devices(self, *, query: str) -> list[IFixitDeviceResult]:
        """Search public iFixit device and category suggestions."""

        results = self._suggest(query=query, doctypes="device,category")
        return [
            IFixitDeviceResult.from_api_item(item)
            for item in results
            if _is_mapping(item)
        ]

    def search_guides(self, *, query: str) -> list[IFixitGuideMetadata]:
        """Search public iFixit guide suggestions without retrieving guide steps."""

        results = self._suggest(query=query, doctypes="guide")
        return [
            IFixitGuideMetadata.from_api_item(item)
            for item in results
            if _is_mapping(item)
        ]

    def get_guide_metadata(self, *, guide_id: int) -> IFixitGuideMetadata | None:
        """Retrieve one lightweight guide summary, never the full guide endpoint."""

        if guide_id < 1:
            raise ValueError("guide_id must be at least 1.")

        params = urlencode({"guideids": guide_id, "limit": 1})
        payload = self._request_json(path=f"/guides?{params}")

        if not isinstance(payload, list):
            raise IFixitApiError("iFixit returned an unexpected guide response.")

        for item in payload:
            if _is_mapping(item):
                metadata = IFixitGuideMetadata.from_api_item(item)
                if metadata.guide_id == guide_id:
                    return metadata

        return None

    def _suggest(self, *, query: str, doctypes: str) -> list[dict[str, Any]]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty.")

        encoded_query = quote(normalized_query, safe="")
        params = urlencode({"doctypes": doctypes})
        payload = self._request_json(path=f"/suggest/{encoded_query}?{params}")

        if not isinstance(payload, dict):
            raise IFixitApiError("iFixit returned an unexpected search response.")

        results = payload.get("results")
        if not isinstance(results, list):
            raise IFixitApiError("iFixit returned an unexpected search response.")

        return [item for item in results if _is_mapping(item)]

    def _request_json(self, *, path: str) -> object:
        normalized_path = path.strip()
        if not normalized_path:
            raise ValueError("path must not be empty.")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path

        request = Request(
            f"{self.base_url}{normalized_path}",
            headers={"Accept": "application/json", "User-Agent": self.USER_AGENT},
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            if exc.code == 429:
                message = "iFixit API rate limit exceeded."
            else:
                message = f"iFixit API request failed with HTTP {exc.code}."
            raise IFixitApiError(message, status_code=exc.code) from exc
        except TimeoutError as exc:
            raise IFixitApiError(
                "iFixit API request timed out.", timed_out=True
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise IFixitApiError(
                    "iFixit API request timed out.", timed_out=True
                ) from exc
            raise IFixitApiError("Unable to connect to the iFixit API.") from exc

        try:
            return json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise IFixitApiError("iFixit returned a non-JSON response.") from exc


def _is_mapping(value: object) -> bool:
    return isinstance(value, dict)
