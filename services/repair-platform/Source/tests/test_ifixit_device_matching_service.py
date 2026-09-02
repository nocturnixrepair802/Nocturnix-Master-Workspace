from __future__ import annotations

import pytest

from integrations.ifixit import (
    IFixitApiError,
    IFixitDeviceResult,
    IFixitGuideMetadata,
)
from services.ifixit_device_matching_service import (
    EXACT_MATCH,
    LIKELY_MATCH,
    NO_MATCH,
    UNCERTAIN_MATCH,
    IFixitDeviceMatchingService,
    normalize_device_identity,
)


def device(title: str, *, category: str | None = None) -> IFixitDeviceResult:
    slug = title.replace(" ", "_")
    return IFixitDeviceResult(
        title=title,
        result_type="device",
        category=category,
        url=f"https://www.ifixit.com/Device/{slug}",
    )


def guide(
    guide_id: int,
    *,
    category: str,
    difficulty: str | None = None,
) -> IFixitGuideMetadata:
    return IFixitGuideMetadata(
        guide_id=guide_id,
        title=f"{category} Screen Replacement",
        category=category,
        subject="Screen",
        guide_type="replacement",
        url=f"https://www.ifixit.com/Guide/example/{guide_id}",
        locale="en",
        author="Technician",
        revision_id=456,
        modified_date=1_700_000_000.0,
        time_required_min=30,
        time_required_max=60,
        difficulty=difficulty,
    )


class FakeIFixitClient:
    def __init__(
        self,
        *,
        devices: list[IFixitDeviceResult] | None = None,
        guides: list[IFixitGuideMetadata] | None = None,
        summaries: dict[int, IFixitGuideMetadata] | None = None,
    ) -> None:
        self.devices = devices or []
        self.guides = guides or []
        self.summaries = summaries or {}
        self.device_queries: list[str] = []
        self.guide_queries: list[str] = []
        self.summary_ids: list[int] = []

    def search_devices(self, *, query: str) -> list[IFixitDeviceResult]:
        self.device_queries.append(query)
        return self.devices

    def search_guides(self, *, query: str) -> list[IFixitGuideMetadata]:
        self.guide_queries.append(query)
        return self.guides

    def get_guide_metadata(self, *, guide_id: int) -> IFixitGuideMetadata | None:
        self.summary_ids.append(guide_id)
        return self.summaries.get(guide_id)


def test_exact_match_retrieves_summary_metadata() -> None:
    search_guide = guide(123, category="iPhone 15")
    summary = guide(123, category="iPhone 15", difficulty="Moderate")
    client = FakeIFixitClient(
        devices=[device("iPhone 15", category="iPhone")],
        guides=[search_guide],
        summaries={123: summary},
    )

    result = IFixitDeviceMatchingService(client).match_device(
        manufacturer="Apple",
        model="iPhone 15",
    )

    assert result.match_classification == EXACT_MATCH
    assert result.confidence == 1.0
    assert result.selected_candidate is not None
    assert result.selected_candidate.url == "https://www.ifixit.com/Device/iPhone_15"
    assert result.guide_summaries == (summary,)
    assert client.device_queries == ["Apple iPhone 15"]
    assert client.guide_queries == ["iPhone 15"]
    assert client.summary_ids == [123]


def test_normalization_handles_punctuation_case_and_manufacturer_duplication() -> None:
    client = FakeIFixitClient(devices=[device("Samsung Galaxy S22 Plus")])

    result = IFixitDeviceMatchingService(client).match_device(
        manufacturer="SAMSUNG Electronics, Inc.",
        model="samsung electronics -- Galaxy S22+",
    )

    assert result.normalized_device.manufacturer == "Samsung"
    assert result.normalized_device.model == "Galaxy S22 Plus"
    assert result.normalized_device.search_query == "Samsung Galaxy S22 Plus"
    assert result.match_classification == EXACT_MATCH


def test_close_top_candidates_are_classified_as_uncertain() -> None:
    client = FakeIFixitClient(
        devices=[
            device("Google Pixel 8 Pro", category="Google Pixel"),
            device("Google Pixel 8 Pro", category="Android Phone"),
        ]
    )

    result = IFixitDeviceMatchingService(client).match_device(
        manufacturer="Google",
        model="Pixel 8",
    )

    assert len(result.candidates) == 2
    assert result.match_classification == UNCERTAIN_MATCH
    assert result.selected_candidate is not None
    assert result.selected_candidate.classification == UNCERTAIN_MATCH
    assert result.selected_candidate.reasons[-1] == (
        "Top candidates are too close to select confidently."
    )


def test_related_model_is_classified_as_likely() -> None:
    client = FakeIFixitClient(devices=[device("iPhone 15 Pro")])

    result = IFixitDeviceMatchingService(client).match_device(
        manufacturer="Apple",
        model="iPhone 15",
    )

    assert result.match_classification == LIKELY_MATCH
    assert result.selected_candidate is not None
    assert result.selected_candidate.classification == LIKELY_MATCH
    assert result.selected_candidate.reasons[0].startswith("Normalized text similarity")


def test_different_model_is_classified_as_uncertain() -> None:
    client = FakeIFixitClient(devices=[device("iPhone 14")])

    result = IFixitDeviceMatchingService(client).match_device(
        manufacturer="Apple",
        model="iPhone 15",
    )

    assert result.match_classification == UNCERTAIN_MATCH
    assert result.selected_candidate is not None
    assert result.selected_candidate.confidence < 0.78


def test_no_candidates_returns_no_match_without_guide_search() -> None:
    client = FakeIFixitClient()

    result = IFixitDeviceMatchingService(client).match_device(
        manufacturer="Apple",
        model="Unknown Phone",
    )

    assert result.match_classification == NO_MATCH
    assert result.confidence == 0.0
    assert result.selected_candidate is None
    assert result.guide_summaries == ()
    assert client.guide_queries == []


def test_exact_override_controls_selection_and_guide_query() -> None:
    client = FakeIFixitClient(devices=[device("iPhone 15 Pro")])

    result = IFixitDeviceMatchingService(client).match_device(
        manufacturer="Apple",
        model="iPhone 15",
        ifixit_device_override="iPhone-15 Pro",
    )

    assert result.override_applied is True
    assert result.normalized_device.model == "iPhone 15"
    assert result.match_classification == EXACT_MATCH
    assert result.selected_candidate is not None
    assert result.selected_candidate.title == "iPhone 15 Pro"
    assert client.device_queries == ["iPhone 15 Pro"]
    assert client.guide_queries == ["iPhone 15 Pro"]


def test_override_requires_an_exact_ifixit_candidate() -> None:
    client = FakeIFixitClient(devices=[device("iPhone 15 Pro Max")])

    result = IFixitDeviceMatchingService(client).match_device(
        manufacturer="Apple",
        model="iPhone 15",
        ifixit_device_override="iPhone 15 Pro",
    )

    assert result.override_applied is True
    assert result.match_classification == NO_MATCH
    assert result.selected_candidate is None
    assert result.guide_summaries == ()


@pytest.mark.parametrize(
    ("manufacturer", "model", "message"),
    [
        ("---", "iPhone 15", "manufacturer must contain letters or numbers"),
        ("Apple", "...", "model must contain letters or numbers"),
        ("Apple", "Apple", "model must include a value beyond the manufacturer"),
    ],
)
def test_invalid_device_identity_is_rejected(
    manufacturer: str,
    model: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        normalize_device_identity(manufacturer=manufacturer, model=model)


def test_upstream_errors_are_not_hidden() -> None:
    class FailingClient(FakeIFixitClient):
        def search_devices(self, *, query: str) -> list[IFixitDeviceResult]:
            del query
            raise IFixitApiError("iFixit API request timed out.", timed_out=True)

    with pytest.raises(IFixitApiError, match="timed out"):
        IFixitDeviceMatchingService(FailingClient()).match_device(
            manufacturer="Apple",
            model="iPhone 15",
        )
