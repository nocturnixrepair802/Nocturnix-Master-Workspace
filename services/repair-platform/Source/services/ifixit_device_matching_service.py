from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, replace
from difflib import SequenceMatcher

from integrations.ifixit import (
    IFixitClient,
    IFixitDeviceResult,
    IFixitGuideMetadata,
)

EXACT_MATCH = "exact"
LIKELY_MATCH = "likely"
UNCERTAIN_MATCH = "uncertain"
NO_MATCH = "no_match"

LIKELY_THRESHOLD = 0.78
AMBIGUITY_MARGIN = 0.05
MAX_GUIDE_SUMMARIES = 5

MANUFACTURER_ALIASES = {
    "apple": "Apple",
    "google": "Google",
    "huawei": "Huawei",
    "lg": "LG",
    "lg electronics": "LG",
    "motorola": "Motorola",
    "motorola mobility": "Motorola",
    "nokia": "Nokia",
    "oneplus": "OnePlus",
    "samsung": "Samsung",
    "samsung electronics": "Samsung",
    "sony": "Sony",
}

COMPANY_SUFFIXES = {
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "incorporated",
    "limited",
    "llc",
    "ltd",
}


@dataclass(frozen=True, slots=True)
class NormalizedDeviceIdentity:
    manufacturer: str
    model: str
    search_query: str
    manufacturer_key: str
    model_key: str

    def to_api_dict(self) -> dict[str, str]:
        return {
            "manufacturer": self.manufacturer,
            "model": self.model,
            "search_query": self.search_query,
        }


@dataclass(frozen=True, slots=True)
class RankedIFixitCandidate:
    title: str
    result_type: str
    category: str | None
    url: str | None
    confidence: float
    classification: str
    reasons: tuple[str, ...]

    def to_api_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["reasons"] = list(self.reasons)
        return data


@dataclass(frozen=True, slots=True)
class IFixitDeviceGuideMatch:
    normalized_device: NormalizedDeviceIdentity
    candidates: tuple[RankedIFixitCandidate, ...]
    selected_candidate: RankedIFixitCandidate | None
    match_classification: str
    confidence: float
    guide_summaries: tuple[IFixitGuideMetadata, ...]
    override_applied: bool

    def to_api_dict(self) -> dict[str, object]:
        return {
            "normalized_device": self.normalized_device.to_api_dict(),
            "candidates": [candidate.to_api_dict() for candidate in self.candidates],
            "selected_candidate": (
                self.selected_candidate.to_api_dict()
                if self.selected_candidate is not None
                else None
            ),
            "match_classification": self.match_classification,
            "confidence": self.confidence,
            "guide_summaries": [
                guide.to_api_dict() for guide in self.guide_summaries
            ],
            "override_applied": self.override_applied,
        }


class IFixitDeviceMatchingService:
    """Connect Nocturnix device identity to read-only iFixit summaries."""

    def __init__(self, client: IFixitClient) -> None:
        self.client = client

    def match_device(
        self,
        *,
        manufacturer: str,
        model: str,
        ifixit_device_override: str | None = None,
    ) -> IFixitDeviceGuideMatch:
        identity = normalize_device_identity(manufacturer=manufacturer, model=model)
        override = _normalize_display(ifixit_device_override or "")

        if ifixit_device_override is not None and not override:
            raise ValueError("ifixit_device_override must not be empty.")

        search_query = override or identity.search_query
        raw_candidates = self.client.search_devices(query=search_query)
        ranked = tuple(
            sorted(
                (
                    self._rank_candidate(
                        identity=identity,
                        candidate=candidate,
                        override=override or None,
                    )
                    for candidate in raw_candidates
                ),
                key=lambda candidate: (-candidate.confidence, candidate.title.casefold()),
            )
        )

        selected = ranked[0] if ranked else None
        if override and (
            selected is None or selected.classification != EXACT_MATCH
        ):
            selected = None

        classification = selected.classification if selected else NO_MATCH
        confidence = selected.confidence if selected else 0.0

        if (
            selected is not None
            and not override
            and selected.classification != EXACT_MATCH
            and len(ranked) > 1
            and selected.confidence - ranked[1].confidence < AMBIGUITY_MARGIN
        ):
            classification = UNCERTAIN_MATCH
            selected = replace(
                selected,
                classification=UNCERTAIN_MATCH,
                reasons=selected.reasons
                + ("Top candidates are too close to select confidently.",),
            )

        guides = self._guide_summaries(selected) if selected is not None else ()

        return IFixitDeviceGuideMatch(
            normalized_device=identity,
            candidates=ranked,
            selected_candidate=selected,
            match_classification=classification,
            confidence=confidence,
            guide_summaries=guides,
            override_applied=bool(override),
        )

    def _rank_candidate(
        self,
        *,
        identity: NormalizedDeviceIdentity,
        candidate: IFixitDeviceResult,
        override: str | None,
    ) -> RankedIFixitCandidate:
        target_key = _comparison_key(override) if override else identity.model_key
        candidate_full_key = _comparison_key(candidate.title)
        candidate_model_key = _remove_manufacturer_prefix(
            candidate_full_key,
            (identity.manufacturer_key,),
        )

        exact = candidate_full_key == target_key or candidate_model_key == target_key
        if exact:
            return RankedIFixitCandidate(
                title=candidate.title,
                result_type=candidate.result_type,
                category=candidate.category,
                url=candidate.url,
                confidence=1.0,
                classification=EXACT_MATCH,
                reasons=("Normalized device text matches exactly.",),
            )

        target_tokens = set(target_key.split())
        candidate_tokens = set(candidate_model_key.split())
        shared_tokens = target_tokens & candidate_tokens

        coverage = len(shared_tokens) / len(target_tokens) if target_tokens else 0.0
        precision = (
            len(shared_tokens) / len(candidate_tokens) if candidate_tokens else 0.0
        )
        similarity = SequenceMatcher(None, target_key, candidate_model_key).ratio()
        manufacturer_tokens = set(identity.manufacturer_key.split())
        manufacturer_present = manufacturer_tokens <= set(candidate_full_key.split())
        manufacturer_evidence = 1.0 if manufacturer_present else 0.5

        confidence = round(
            0.45 * similarity
            + 0.35 * coverage
            + 0.15 * precision
            + 0.05 * manufacturer_evidence,
            4,
        )
        classification = LIKELY_MATCH if confidence >= LIKELY_THRESHOLD else UNCERTAIN_MATCH
        reasons = (
            f"Normalized text similarity: {similarity:.2f}.",
            f"Model token coverage: {coverage:.2f}.",
            f"Candidate token precision: {precision:.2f}.",
            (
                "Manufacturer appears in the candidate."
                if manufacturer_present
                else "Candidate omits the manufacturer name."
            ),
        )

        return RankedIFixitCandidate(
            title=candidate.title,
            result_type=candidate.result_type,
            category=candidate.category,
            url=candidate.url,
            confidence=confidence,
            classification=classification,
            reasons=reasons,
        )

    def _guide_summaries(
        self,
        candidate: RankedIFixitCandidate,
    ) -> tuple[IFixitGuideMetadata, ...]:
        suggestions = self.client.search_guides(query=candidate.title)
        category_keys = {
            _comparison_key(value)
            for value in (candidate.title, candidate.category)
            if value
        }
        matching = [
            guide
            for guide in suggestions
            if guide.category and _comparison_key(guide.category) in category_keys
        ]

        summaries: list[IFixitGuideMetadata] = []
        seen_ids: set[int] = set()
        for guide in matching:
            if len(summaries) >= MAX_GUIDE_SUMMARIES:
                break
            if guide.guide_id is None or guide.guide_id in seen_ids:
                continue

            summary = self.client.get_guide_metadata(guide_id=guide.guide_id)
            if summary is not None:
                summaries.append(summary)
                seen_ids.add(guide.guide_id)

        return tuple(summaries)


def normalize_device_identity(
    *,
    manufacturer: str,
    model: str,
) -> NormalizedDeviceIdentity:
    normalized_manufacturer, manufacturer_keys = _normalize_manufacturer(manufacturer)
    normalized_model = _normalize_display(model)

    if not normalized_manufacturer:
        raise ValueError("manufacturer must contain letters or numbers.")
    if not normalized_model:
        raise ValueError("model must contain letters or numbers.")

    model_key = _remove_manufacturer_prefix(
        _comparison_key(normalized_model),
        manufacturer_keys,
    )
    if not model_key:
        raise ValueError("model must include a value beyond the manufacturer name.")

    model_tokens = model_key.split()
    normalized_model = _display_tokens_from_source(normalized_model, model_tokens)

    return NormalizedDeviceIdentity(
        manufacturer=normalized_manufacturer,
        model=normalized_model,
        search_query=f"{normalized_manufacturer} {normalized_model}",
        manufacturer_key=_comparison_key(normalized_manufacturer),
        model_key=model_key,
    )


def _normalize_manufacturer(value: str) -> tuple[str, tuple[str, ...]]:
    display = _normalize_display(value)
    key = _comparison_key(display)
    if not key:
        return "", ()

    tokens = key.split()
    stripped_tokens = list(tokens)
    while stripped_tokens and stripped_tokens[-1] in COMPANY_SUFFIXES:
        stripped_tokens.pop()
    stripped_key = " ".join(stripped_tokens)

    canonical = MANUFACTURER_ALIASES.get(key) or MANUFACTURER_ALIASES.get(stripped_key)
    normalized = canonical or display
    keys = tuple(
        dict.fromkeys(
            candidate
            for candidate in (key, stripped_key, _comparison_key(normalized))
            if candidate
        )
    )
    return normalized, keys


def _normalize_display(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    normalized = (
        normalized.replace("_", " ").replace("+", " Plus ").replace("&", " and ")
    )
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def _comparison_key(value: str) -> str:
    return _normalize_display(value).casefold()


def _remove_manufacturer_prefix(value: str, manufacturer_keys: tuple[str, ...]) -> str:
    tokens = value.split()
    prefixes = [key.split() for key in manufacturer_keys if key]
    removed = True
    while removed and tokens:
        removed = False
        for prefix in sorted(prefixes, key=len, reverse=True):
            if tokens[: len(prefix)] == prefix:
                tokens = tokens[len(prefix) :]
                removed = True
                break
    return " ".join(tokens)


def _display_tokens_from_source(source: str, remaining_tokens: list[str]) -> str:
    source_tokens = source.split()
    if len(source_tokens) >= len(remaining_tokens):
        return " ".join(source_tokens[-len(remaining_tokens) :])
    return " ".join(remaining_tokens)
