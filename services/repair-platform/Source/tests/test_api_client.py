from __future__ import annotations

import json
from typing import Any

import pytest

import desktop.services.api_client as api_client_module
from desktop.services.api_client import ApiClient
from desktop.services.settings_service import DesktopSettings


class FakeResponse:
    def __init__(
        self,
        payload: bytes,
    ) -> None:
        self._payload = payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def test_health_returns_available_for_ok_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps(
        {
            "status": "ok",
            "service": "repair-platform",
        }
    ).encode("utf-8")

    def fake_urlopen(
        url: str,
        timeout: float,
    ) -> FakeResponse:
        assert url == "http://127.0.0.1:8000/health"
        assert timeout == 2.0

        return FakeResponse(payload)

    monkeypatch.setattr(
        api_client_module,
        "urlopen",
        fake_urlopen,
    )

    client = ApiClient(DesktopSettings())

    result = client.health()

    assert result.available is True
    assert result.status == "ok"
    assert result.service == "repair-platform"
    assert result.url == "http://127.0.0.1:8000/health"
    assert result.error == ""


def test_health_returns_unavailable_when_server_cannot_be_reached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(
        url: str,
        timeout: float,
    ) -> FakeResponse:
        raise api_client_module.URLError("connection refused")

    monkeypatch.setattr(
        api_client_module,
        "urlopen",
        fake_urlopen,
    )

    client = ApiClient(DesktopSettings())

    result = client.health()

    assert result.available is False
    assert result.status == "unavailable"
    assert result.service == ""
    assert result.url == "http://127.0.0.1:8000/health"
    assert result.error


def test_health_returns_unavailable_for_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(
        url: str,
        timeout: float,
    ) -> FakeResponse:
        return FakeResponse(b"not-json")

    monkeypatch.setattr(
        api_client_module,
        "urlopen",
        fake_urlopen,
    )

    client = ApiClient(DesktopSettings())

    result = client.health()

    assert result.available is False
    assert result.status == "unavailable"
    assert result.service == ""
    assert result.url == "http://127.0.0.1:8000/health"
    assert result.error


def test_health_returns_unavailable_for_non_ok_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps(
        {
            "status": "degraded",
            "service": "repair-platform",
        }
    ).encode("utf-8")

    def fake_urlopen(
        url: str,
        timeout: float,
    ) -> FakeResponse:
        return FakeResponse(payload)

    monkeypatch.setattr(
        api_client_module,
        "urlopen",
        fake_urlopen,
    )

    client = ApiClient(DesktopSettings())

    result = client.health()

    assert result.available is False
    assert result.status == "degraded"
    assert result.service == "repair-platform"
    assert result.url == "http://127.0.0.1:8000/health"
    assert result.error == ""


def test_api_client_normalizes_base_url() -> None:
    client = ApiClient(
        DesktopSettings(
            api_base_url="http://127.0.0.1:8000/",
            api_timeout_seconds=3.5,
        )
    )

    assert client.base_url == "http://127.0.0.1:8000"
    assert client.timeout_seconds == 3.5
