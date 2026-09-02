from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import api.app as api_app
from integrations.ifixit import (
    IFixitApiError,
    IFixitDeviceResult,
    IFixitGuideMetadata,
)

GUIDE = IFixitGuideMetadata(
    guide_id=123,
    title="iPhone 15 Screen Replacement",
    category="iPhone 15",
    subject="Screen",
    guide_type="replacement",
    url="https://www.ifixit.com/Guide/example/123",
    locale="en",
    author="Technician",
    revision_id=456,
    modified_date=1_700_000_000.0,
    time_required_min=30,
    time_required_max=60,
    difficulty="Moderate",
)


class FakeIFixitClient:
    def search_devices(self, *, query: str) -> list[IFixitDeviceResult]:
        assert query in {"iPhone 15", "Apple iPhone 15"}
        return [
            IFixitDeviceResult(
                title="iPhone 15",
                result_type="device",
                category="iPhone",
                url="https://www.ifixit.com/Device/iPhone_15",
            )
        ]

    def search_guides(self, *, query: str) -> list[IFixitGuideMetadata]:
        assert query in {"iPhone 15 screen", "iPhone 15"}
        return [GUIDE]

    def get_guide_metadata(self, *, guide_id: int) -> IFixitGuideMetadata | None:
        return GUIDE if guide_id == 123 else None


@pytest.fixture
def client() -> TestClient:
    api_app.app.dependency_overrides[api_app.get_ifixit_client] = FakeIFixitClient
    with TestClient(api_app.app) as test_client:
        yield test_client
    api_app.app.dependency_overrides.clear()


def test_device_search_returns_normalized_results_and_attribution(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/integrations/ifixit/devices/search", params={"q": "iPhone 15"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["returned_items"] == 1
    assert payload["items"][0]["result_type"] == "device"
    assert payload["attribution"]["provider"] == "iFixit"
    assert "image" not in payload["items"][0]


def test_guide_search_returns_metadata_only(client: TestClient) -> None:
    response = client.get(
        "/api/v1/integrations/ifixit/guides/search",
        params={"q": "iPhone 15 screen"},
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["guide_id"] == 123
    assert item["difficulty"] == "Moderate"
    assert "steps" not in item
    assert "introduction" not in item


def test_get_guide_returns_metadata(client: TestClient) -> None:
    response = client.get("/api/v1/integrations/ifixit/guides/123")

    assert response.status_code == 200
    assert response.json()["guide"]["url"].endswith("/123")


def test_get_guide_returns_404_for_missing_summary(client: TestClient) -> None:
    response = client.get("/api/v1/integrations/ifixit/guides/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "iFixit guide was not found."}


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (IFixitApiError("iFixit API request timed out.", timed_out=True), 504),
        (IFixitApiError("iFixit API request failed with HTTP 500."), 502),
        (IFixitApiError("iFixit API rate limit exceeded.", status_code=429), 503),
    ],
)
def test_upstream_errors_map_to_safe_api_responses(
    client: TestClient,
    error: IFixitApiError,
    status_code: int,
) -> None:
    class FailingClient(FakeIFixitClient):
        def search_guides(self, *, query: str) -> list[IFixitGuideMetadata]:
            del query
            raise error

    api_app.app.dependency_overrides[api_app.get_ifixit_client] = FailingClient
    response = client.get(
        "/api/v1/integrations/ifixit/guides/search", params={"q": "screen"}
    )

    assert response.status_code == status_code
    assert response.json() == {"detail": str(error)}


def test_search_query_validation_happens_before_upstream_call(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/integrations/ifixit/devices/search", params={"q": ""}
    )

    assert response.status_code == 422


def test_device_guide_match_combines_ranked_candidate_and_summaries(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/integrations/ifixit/device-guide-match",
        params={"manufacturer": "Apple", "model": "Apple iPhone-15"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["normalized_device"] == {
        "manufacturer": "Apple",
        "model": "iPhone 15",
        "search_query": "Apple iPhone 15",
    }
    assert payload["match_classification"] == "exact"
    assert payload["confidence"] == 1.0
    assert payload["selected_candidate"]["title"] == "iPhone 15"
    assert payload["guide_summaries"][0]["guide_id"] == 123
    assert payload["attribution"]["provider"] == "iFixit"
    assert "steps" not in payload["guide_summaries"][0]


def test_device_guide_match_maps_upstream_timeout(client: TestClient) -> None:
    class FailingClient(FakeIFixitClient):
        def search_devices(self, *, query: str) -> list[IFixitDeviceResult]:
            del query
            raise IFixitApiError("iFixit API request timed out.", timed_out=True)

    api_app.app.dependency_overrides[api_app.get_ifixit_client] = FailingClient
    response = client.get(
        "/api/v1/integrations/ifixit/device-guide-match",
        params={"manufacturer": "Apple", "model": "iPhone 15"},
    )

    assert response.status_code == 504
    assert response.json() == {"detail": "iFixit API request timed out."}


def test_device_guide_match_requires_manufacturer_and_model(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/integrations/ifixit/device-guide-match",
        params={"manufacturer": "Apple"},
    )

    assert response.status_code == 422
