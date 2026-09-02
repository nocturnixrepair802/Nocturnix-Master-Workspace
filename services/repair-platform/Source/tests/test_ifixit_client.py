from __future__ import annotations

import io
from urllib.error import HTTPError, URLError

import pytest

import integrations.ifixit.client as client_module
from integrations.ifixit import IFixitApiError, IFixitClient


class FakeResponse:
    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body.encode("utf-8")


def test_search_devices_builds_encoded_public_suggest_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, *, timeout: float) -> FakeResponse:
        captured["url"] = request.full_url  # type: ignore[attr-defined]
        captured["timeout"] = timeout
        return FakeResponse(
            '{"results":[{"dataType":"device","title":"iPhone 15",'
            '"category":"iPhone","url":"https://www.ifixit.com/Device/iPhone_15"}]}'
        )

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)
    client = IFixitClient(base_url="https://example.test/api/2.0", timeout_seconds=4)

    results = client.search_devices(query="iPhone 15")

    assert captured == {
        "url": (
            "https://example.test/api/2.0/suggest/iPhone%2015?"
            "doctypes=device%2Ccategory"
        ),
        "timeout": 4,
    }
    assert results[0].title == "iPhone 15"
    assert results[0].result_type == "device"
    assert results[0].url == "https://www.ifixit.com/Device/iPhone_15"


def test_search_guides_normalizes_metadata_and_excludes_image_and_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = """{
      "results": [{
        "guideid": 123,
        "dataType": "guide",
        "title": "iPhone 15 Screen Replacement",
        "category": "iPhone 15",
        "subject": "Screen",
        "type": "replacement",
        "url": "https://www.ifixit.com/Guide/example/123",
        "username": "Technician",
        "image": {"original": "https://example.test/full.jpg"},
        "steps": [{"lines": ["restricted content"]}]
      }]
    }"""
    monkeypatch.setattr(
        client_module, "urlopen", lambda *args, **kwargs: FakeResponse(body)
    )

    guide = IFixitClient().search_guides(query="iPhone screen")[0]
    normalized = guide.to_api_dict()

    assert normalized["guide_id"] == 123
    assert normalized["subject"] == "Screen"
    assert "image" not in normalized
    assert "steps" not in normalized


def test_get_guide_metadata_uses_summary_list_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_url = ""

    def fake_urlopen(request: object, *, timeout: float) -> FakeResponse:
        nonlocal captured_url
        del timeout
        captured_url = request.full_url  # type: ignore[attr-defined]
        return FakeResponse(
            '[{"guideid":123,"title":"Screen Replacement",'
            '"difficulty":{"name":"Moderate"},"time_required_min":30}]'
        )

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    guide = IFixitClient().get_guide_metadata(guide_id=123)

    assert captured_url.endswith("/guides?guideids=123&limit=1")
    assert "/guides/123" not in captured_url
    assert guide is not None
    assert guide.difficulty == "Moderate"
    assert guide.time_required_min == 30


@pytest.mark.parametrize(
    ("error", "expected_message", "timed_out"),
    [
        (TimeoutError(), "iFixit API request timed out.", True),
        (URLError(TimeoutError()), "iFixit API request timed out.", True),
        (URLError("offline"), "Unable to connect to the iFixit API.", False),
    ],
)
def test_connection_errors_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_message: str,
    timed_out: bool,
) -> None:
    def fake_urlopen(*args: object, **kwargs: object) -> FakeResponse:
        raise error

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    with pytest.raises(IFixitApiError, match=expected_message) as caught:
        IFixitClient().search_devices(query="phone")

    assert caught.value.timed_out is timed_out


def test_http_error_does_not_expose_upstream_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = HTTPError(
        "https://example.test",
        500,
        "error",
        hdrs=None,
        fp=io.BytesIO(b"upstream internal details"),
    )
    monkeypatch.setattr(
        client_module,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    with pytest.raises(IFixitApiError) as caught:
        IFixitClient().search_guides(query="screen")

    assert str(caught.value) == "iFixit API request failed with HTTP 500."
    assert "internal details" not in str(caught.value)


@pytest.mark.parametrize("body", ["not json", "[]", '{"results":{}}'])
def test_search_rejects_invalid_upstream_responses(
    monkeypatch: pytest.MonkeyPatch,
    body: str,
) -> None:
    monkeypatch.setattr(
        client_module, "urlopen", lambda *args, **kwargs: FakeResponse(body)
    )

    with pytest.raises(IFixitApiError):
        IFixitClient().search_devices(query="phone")
