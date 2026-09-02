from __future__ import annotations

import json
import re
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

import integrations.mobilesentrix.workbook_sync as workbook_sync
from integrations.mobilesentrix import (
    MobileSentrixWorkbookSyncService,
)
from integrations.mobilesentrix.client import (
    MobileSentrixApiError,
    MobileSentrixClient,
)
from integrations.mobilesentrix.models import (
    MobileSentrixDetailedProduct,
    MobileSentrixProduct,
)

# ============================================================
# Investigator configuration
# ============================================================

MAX_UNMATCHED_ITEMS = 289

SEARCH_MAX_RESULTS = 25

REQUEST_DELAY_SECONDS = 0.20

MIN_STRONG_SCORE = 0.82
MIN_POSSIBLE_SCORE = 0.65
MIN_VIABLE_SCORE = 0.50


MAX_DETAILED_CANDIDATES = 5

MAX_SEARCH_QUERIES_PER_ITEM = 5


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

REPORT_DIR = BASE_DIR / "Data" / "reports"

RUN_TIMESTAMP = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

REPORT_PATH = REPORT_DIR / f"mobilesentrix_unmatched_{RUN_TIMESTAMP}.json"


# ============================================================
# Result models
# ============================================================


@dataclass(slots=True)
class CandidateResult:
    product_id: str | None
    sku: str | None
    title: str | None

    search_price: str | None
    search_in_stock: bool | None

    title_similarity: float
    manufacturer_match: bool
    model_overlap: float

    region_voltage_match: bool | None
    pack_match: bool | None
    packaging_type_match: bool | None
    color_match: bool | None
    grade_match: bool | None

    quality_tier_match: bool | None
    exact_device_match: bool | None
    compatibility_product: bool

    score: float

    reasons: list[str]

    detailed_product: dict[str, object] | None


@dataclass(slots=True)
class InvestigationResult:
    workbook_row: int
    old_sku: str

    old_product_name: str | None
    old_manufacturer: str | None
    old_device_model: str | None
    old_category: str | None
    old_unit_cost: str | None

    search_queries: list[str]

    outcome: str

    selected_candidate: CandidateResult | None

    candidates: list[CandidateResult]

    error: str | None


# ============================================================
# Text utilities
# ============================================================


def normalize_text(
    value: object,
) -> str:
    if value is None:
        return ""

    text = str(value).lower()

    text = text.replace("&", " and ")

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return " ".join(text.split())


def title_similarity(
    first: object,
    second: object,
) -> float:
    left = normalize_text(first)
    right = normalize_text(second)

    if not left or not right:
        return 0.0

    return SequenceMatcher(
        None,
        left,
        right,
    ).ratio()


def contains_text(
    haystack: object,
    needle: object,
) -> bool:
    normalized_haystack = normalize_text(haystack)

    normalized_needle = normalize_text(needle)

    if not normalized_needle:
        return False

    return normalized_needle in normalized_haystack


def remove_parenthetical_noise(
    value: str,
) -> str:
    """
    Remove parenthetical fragments that are usually attributes rather
    than core product identity.

    Manufacturer names are intentionally not removed universally,
    because they can be useful search terms.
    """

    text = value

    removable_patterns = [
        r"\((?:retail pack)\)",
        r"\((?:clear|black|white|green|blue|red|pink|purple|gold|silver)\)",
        r"\((?:used oem pull:[^)]+)\)",
        r"\((?:grade [abc])\)",
    ]

    for pattern in removable_patterns:
        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE,
        )

    return " ".join(text.split())


def strip_secondary_attributes(
    value: str,
) -> str:
    text = remove_parenthetical_noise(value)

    patterns = [
        r"\b(?:10|20|25|50|100)\s*pack\b",
        r"\bretail\s+pack\b",
        r"\bclear\b",
        r"\bblack\b",
        r"\bwhite\b",
        r"\bgreen\b",
        r"\bblue\b",
        r"\bred\b",
        r"\bpink\b",
        r"\bpurple\b",
        r"\bgold\b",
        r"\bsilver\b",
        r"\bgrade\s+[abc]\b",
    ]

    for pattern in patterns:
        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip(" -/(),")


def build_core_query(
    product_name: str,
    manufacturer: str | None,
) -> str:
    text = product_name

    # Remove parenthetical attribute blocks.
    text = re.sub(
        r"\([^)]*\)",
        " ",
        text,
    )

    # Remove compatibility ranges introduced by W/ or With.
    text = re.sub(
        r"\b(?:w\s*/|with)\s+iphone\b.*$",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # Remove common secondary attributes.
    patterns = [
        r"\bretail\s+pack\b",
        r"\b\d+\s*pack\b",
        r"\bused\s+oem\s+pull\b",
        r"\bgrade\s+[abc]\b",
        r"\b110v\b",
        r"\b120v\b",
        r"\b220v\b",
        r"\bnorth\s+american\b",
        r"\bnorth\s+america\b",
        r"\beurope(?:an)?\b",
        r"\bclear\b",
        r"\bblack\b",
        r"\bwhite\b",
        r"\bgreen\b",
        r"\bblue\b",
        r"\bred\b",
        r"\bpink\b",
        r"\bpurple\b",
        r"\bgold\b",
        r"\bsilver\b",
    ]

    for pattern in patterns:
        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE,
        )

    text = text.replace(
        "&",
        " ",
    )

    text = text.replace(
        "/",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip(" -(),")

    words = text.split()

    # Keep the product-family portion concise.
    if len(words) > 8:
        words = words[:8]

    query = " ".join(words).strip()

    if manufacturer:
        normalized_query = normalize_text(query)

        normalized_manufacturer = normalize_text(manufacturer)

        if normalized_manufacturer and normalized_manufacturer not in normalized_query:
            query = (f"{query} {manufacturer}").strip()

    return query


def generate_search_queries(
    *,
    product_name: str,
    manufacturer: str | None,
) -> list[str]:
    queries: list[str] = []

    def add_query(
        value: str | None,
    ) -> None:
        if not value:
            return

        cleaned = " ".join(value.split()).strip()

        if not cleaned:
            return

        normalized = normalize_text(cleaned)

        for existing in queries:
            if normalize_text(existing) == normalized:
                return

        queries.append(cleaned)

    # 1. Original supplier title.
    add_query(product_name)

    # 2. Remove obvious parenthetical noise.
    add_query(remove_parenthetical_noise(product_name))

    # 3. Remove secondary attributes.
    add_query(strip_secondary_attributes(product_name))

    # 4. Core product-family query.
    core_query = build_core_query(
        product_name,
        manufacturer,
    )

    add_query(core_query)

    # 5. Shortened core query.
    core_words = core_query.split()

    if len(core_words) > 6:
        short_core = " ".join(core_words[:6])

        if manufacturer:
            normalized_short = normalize_text(short_core)

            normalized_manufacturer = normalize_text(manufacturer)

            if (
                normalized_manufacturer
                and normalized_manufacturer not in normalized_short
            ):
                short_core = f"{short_core} " f"{manufacturer}"

        add_query(short_core)

    return queries[:MAX_SEARCH_QUERIES_PER_ITEM]


# ============================================================
# Attribute extraction
# ============================================================


def extract_pack_size(
    value: object,
) -> int | None:
    text = normalize_text(value)

    patterns = [
        r"\b(\d+)\s*pack\b",
        r"\bpack\s+of\s+(\d+)\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

    return None


def extract_packaging_type(
    value: object,
) -> str | None:
    text = normalize_text(value)

    if re.search(
        r"\bretail\s+pack\b",
        text,
    ):
        return "retail_pack"

    pack_size = extract_pack_size(value)

    if pack_size is not None:
        return f"bulk_pack_{pack_size}"

    return None


def compare_packaging_type(
    old_name: object,
    candidate_name: object,
) -> bool | None:
    old_type = extract_packaging_type(old_name)

    candidate_type = extract_packaging_type(candidate_name)

    if old_type is None:
        return None

    if candidate_type is None:
        return False

    return old_type == candidate_type


def compare_pack_size(
    old_name: object,
    candidate_name: object,
) -> bool | None:
    old_pack = extract_pack_size(old_name)

    candidate_pack = extract_pack_size(candidate_name)

    if old_pack is None:
        return None

    if candidate_pack is None:
        return False

    return old_pack == candidate_pack


def extract_region_voltage_tokens(
    value: object,
) -> set[str]:
    text = normalize_text(value)

    tokens: set[str] = set()

    patterns = {
        "110v": (
            "110v",
            "110 v",
        ),
        "120v": (
            "120v",
            "120 v",
        ),
        "220v": (
            "220v",
            "220 v",
        ),
        "north_american": (
            "north american",
            "north america",
            "usa",
            "us version",
        ),
        "europe": (
            "europe",
            "european",
            "eu version",
        ),
    }

    for canonical, variants in patterns.items():
        for variant in variants:
            if normalize_text(variant) in text:
                tokens.add(canonical)
                break

    return tokens


def region_voltage_match(
    old_name: object,
    candidate_name: object,
) -> bool | None:
    old_tokens = extract_region_voltage_tokens(old_name)

    candidate_tokens = extract_region_voltage_tokens(candidate_name)

    if not old_tokens:
        return None

    if not candidate_tokens:
        return False

    return old_tokens.issubset(candidate_tokens)


def extract_color(
    value: object,
) -> str | None:
    text = normalize_text(value)

    colors = [
        "clear",
        "black",
        "white",
        "green",
        "blue",
        "red",
        "pink",
        "purple",
        "gold",
        "silver",
        "gray",
        "grey",
        "orange",
        "yellow",
    ]

    for color in colors:
        if re.search(
            rf"\b{re.escape(color)}\b",
            text,
        ):
            return color

    return None


def compare_color(
    old_name: object,
    candidate_name: object,
) -> bool | None:
    old_color = extract_color(old_name)

    candidate_color = extract_color(candidate_name)

    if old_color is None:
        return None

    if candidate_color is None:
        return False

    if old_color == "gray" and candidate_color == "grey":
        return True

    if old_color == "grey" and candidate_color == "gray":
        return True

    return old_color == candidate_color


def extract_grade(
    value: object,
) -> str | None:
    text = normalize_text(value)

    match = re.search(
        r"\bgrade\s+([abc])\b",
        text,
    )

    if not match:
        return None

    return match.group(1).upper()


def compare_grade(
    old_name: object,
    candidate_name: object,
) -> bool | None:
    old_grade = extract_grade(old_name)

    candidate_grade = extract_grade(candidate_name)

    if old_grade is None:
        return None

    if candidate_grade is None:
        return False

    return old_grade == candidate_grade


def extract_quality_tier(
    value: object,
) -> str | None:
    """
    Extract the product quality / sourcing tier from a title.

    These are materially different supplier products and should not
    automatically replace one another.
    """

    text = normalize_text(value)

    quality_patterns = [
        ("genuine_oem", r"\bgenuine\s+oem\b"),
        ("used_oem_pull", r"\bused\s+oem\s+pull\b"),
        ("refurbished", r"\brefurbished\b"),
        ("aftermarket_plus", r"\baftermarket\s+plus\b"),
        ("aftermarket", r"\baftermarket\b"),
        ("premium", r"\bpremium\b"),
        ("service_pack", r"\bservice\s+pack\b"),
        ("ampsentrix_pro", r"\bampsentrix\s+pro\b"),
        ("ampsentrix_core", r"\bampsentrix\s+core\b"),
    ]

    for quality_name, pattern in quality_patterns:
        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return quality_name

    return None


def compare_quality_tier(
    old_name: object,
    candidate_name: object,
) -> bool | None:
    old_quality = extract_quality_tier(old_name)

    candidate_quality = extract_quality_tier(candidate_name)

    if old_quality is None:
        return None

    if candidate_quality is None:
        return False

    return old_quality == candidate_quality


def is_compatibility_product(
    *,
    product_name: object,
    category: object,
) -> bool:
    """
    Identify products whose purpose is to support multiple device
    models rather than being a model-specific replacement component.

    Compatibility expansion is acceptable for these items when the
    original supported model remains included.
    """

    name = normalize_text(product_name)

    category_text = normalize_text(category)

    compatibility_terms = (
        "repair tool",
        "repair tools",
        "board holder",
        "preheater",
        "desoldering station",
        "soldering station",
        "programmer",
        "fixture",
        "separator",
        "tester",
        "testing tool",
        "charging station",
        "tool",
    )

    combined = f"{name} {category_text}"

    return any(term in combined for term in compatibility_terms)


def extract_device_identity(
    value: object,
) -> str | None:
    """
    Extract a model identity from a product title.

    This intentionally preserves meaningful variant words such as
    Pro, Pro Max, Plus, Mini, Ultra, Air, XL, FE, etc.
    """

    text = str(value or "").strip()

    if not text:
        return None

    patterns = [
        # Apple
        r"\biPhone\s+\d+(?:\s+(?:Pro\s+Max|Pro|Plus|Mini|e))?\b",
        # Google Pixel
        r"\bPixel\s+\d+(?:\s+(?:Pro\s+XL|Pro|XL|a|Fold))?\b",
        # Samsung Galaxy Note
        r"\bGalaxy\s+Note\s+\d+(?:\s+Ultra)?(?:\s+5G)?\b",
        # Samsung Galaxy S
        r"\bGalaxy\s+S\d+(?:\s+(?:Ultra|Plus|FE))?(?:\s+5G)?\b",
        # Samsung Galaxy A
        r"\bGalaxy\s+A\d+(?:\s+5G)?\b",
        # Samsung Galaxy J
        r"\bGalaxy\s+J\d+(?:\s+[A-Za-z0-9]+)?\b",
        # Xiaomi / Redmi
        r"\bRedmi\s+Note\s+\d+(?:\s+(?:Pro|Pro\+|Plus|5G))?\b",
        # Asus ROG
        r"\bROG\s+Phone\s+\d+(?:\s+(?:Pro|Ultimate|S|s))?\b",
        # Nokia
        r"\bNokia\s+\d+(?:\.\d+)?\b",
        # LG
        r"\bLG\s+[A-Z0-9]+\b",
        # MacBook model numbers
        r"\bA\d{4}\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return normalize_text(match.group(0))

    return None


def compare_exact_device_identity(
    *,
    old_name: object,
    candidate_name: object,
    compatibility_product: bool,
) -> bool | None:
    """
    Compare device identities.

    For compatibility tools, expanded compatibility is acceptable and
    therefore this check is not treated as a strict identity rule.
    """

    if compatibility_product:
        return None

    old_device = extract_device_identity(old_name)

    candidate_device = extract_device_identity(candidate_name)

    if old_device is None:
        return None

    if candidate_device is None:
        return False

    return old_device == candidate_device


# ============================================================
# Detailed candidate evidence
# ============================================================


def model_overlap_score(
    old_model: object,
    detailed: MobileSentrixDetailedProduct | None,
) -> float:
    if detailed is None:
        return 0.0

    normalized_old_model = normalize_text(old_model)

    if not normalized_old_model:
        return 0.0

    if not detailed.model_names:
        return 0.0

    for model_name in detailed.model_names:
        if normalize_text(model_name) == normalized_old_model:
            return 1.0

    for model_name in detailed.model_names:
        candidate_model = normalize_text(model_name)

        if (
            normalized_old_model in candidate_model
            or candidate_model in normalized_old_model
        ):
            return 0.8

    return 0.0


def manufacturer_matches(
    old_manufacturer: object,
    detailed: MobileSentrixDetailedProduct | None,
    candidate_title: object,
) -> bool:
    normalized_old = normalize_text(old_manufacturer)

    if not normalized_old:
        return False

    if detailed is not None:
        detailed_manufacturer = normalize_text(detailed.manufacturer_text)

        if detailed_manufacturer and detailed_manufacturer == normalized_old:
            return True

    return contains_text(
        candidate_title,
        old_manufacturer,
    )


def safe_string(
    value: object,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def has_critical_identity_mismatch(
    *,
    old_name: object,
    candidate_name: object,
) -> tuple[bool, list[str]]:
    """
    Detect product differences that make two supplier listings unsafe
    automatic replacements even when their titles are otherwise very
    similar.

    Returns:
        (has_mismatch, reasons)
    """

    old_text = normalize_text(old_name)

    candidate_text = normalize_text(candidate_name)

    reasons: list[str] = []

    # --------------------------------------------------------
    # Device / model-number identifiers
    # --------------------------------------------------------

    identifier_patterns = [
        # Apple / MacBook identifiers
        r"\ba\d{4}\b",
        # Samsung-style model codes
        r"\b[a-z]\d{3,4}[a-z]?\b",
        # Pixel / device generation numbers are handled separately,
        # but explicit codes should still be protected.
        r"\bx\d{3}\b",
        # Battery / supplier part numbers such as EB-BX516ABY
        r"\beb[-\s]?[a-z0-9]+\b",
    ]

    for pattern in identifier_patterns:
        old_ids = set(
            re.findall(
                pattern,
                old_text,
                flags=re.IGNORECASE,
            )
        )

        candidate_ids = set(
            re.findall(
                pattern,
                candidate_text,
                flags=re.IGNORECASE,
            )
        )

        if old_ids and candidate_ids and old_ids.isdisjoint(candidate_ids):
            reasons.append(
                "model/part identifier mismatch: "
                f"{sorted(old_ids)} vs "
                f"{sorted(candidate_ids)}"
            )

    # --------------------------------------------------------
    # Important device variants
    # --------------------------------------------------------

    variant_pairs = [
        ("pro max", "pro"),
        ("pro xl", "pro"),
        ("plus", "base"),
        ("ultra", "base"),
        ("mini", "base"),
        ("edge", "base"),
        ("compact", "base"),
        ("pro", "base"),
    ]

    def has_word(
        text: str,
        phrase: str,
    ) -> bool:
        return bool(
            re.search(
                rf"\b{re.escape(phrase)}\b",
                text,
            )
        )

    # S6 vs S6 Edge, 7T vs 7T Pro, etc.
    important_variants = [
        "pro max",
        "pro xl",
        "pro",
        "plus",
        "ultra",
        "mini",
        "edge",
        "compact",
        "xl",
    ]

    for variant in important_variants:
        old_has = has_word(
            old_text,
            variant,
        )

        candidate_has = has_word(
            candidate_text,
            variant,
        )

        if old_has != candidate_has:
            reasons.append(f"device variant mismatch: {variant}")

    # --------------------------------------------------------
    # Explicit regional version
    # --------------------------------------------------------

    old_international = "international version" in old_text

    candidate_international = "international version" in candidate_text

    old_us = "us version" in old_text or "usa version" in old_text

    candidate_us = "us version" in candidate_text or "usa version" in candidate_text

    if old_international and candidate_us:
        reasons.append("regional version mismatch: " "International vs US")

    if old_us and candidate_international:
        reasons.append("regional version mismatch: " "US vs International")

    # --------------------------------------------------------
    # Color substitutions
    # --------------------------------------------------------

    old_color = extract_color(old_name)

    candidate_color = extract_color(candidate_name)

    if old_color and candidate_color and old_color != candidate_color:
        reasons.append("product color mismatch: " f"{old_color} vs {candidate_color}")

    return (
        bool(reasons),
        reasons,
    )


# ============================================================
# Scoring
# ============================================================


def score_candidate(
    *,
    old_name: str | None,
    old_manufacturer: str | None,
    old_model: str | None,
    old_category: str | None,
    search_product: MobileSentrixProduct,
    detailed_product: MobileSentrixDetailedProduct | None,
) -> tuple[
    float,
    float,
    bool,
    float,
    bool | None,
    bool | None,
    bool | None,
    bool | None,
    bool | None,
    bool | None,
    bool | None,
    bool,
    list[str],
]:
    reasons: list[str] = []

    similarity = title_similarity(
        old_name,
        search_product.name,
    )

    manufacturer_match = manufacturer_matches(
        old_manufacturer,
        detailed_product,
        search_product.name,
    )

    model_overlap = model_overlap_score(
        old_model,
        detailed_product,
    )

    regional_match = region_voltage_match(
        old_name,
        search_product.name,
    )

    pack_match = compare_pack_size(
        old_name,
        search_product.name,
    )

    packaging_type_match = compare_packaging_type(
        old_name,
        search_product.name,
    )

    color_match = compare_color(
        old_name,
        search_product.name,
    )

    grade_match = compare_grade(
        old_name,
        search_product.name,
    )

    quality_tier_match = compare_quality_tier(
        old_name,
        search_product.name,
    )

    compatibility_product = is_compatibility_product(
        product_name=old_name,
        category=old_category,
    )

    exact_device_match = compare_exact_device_identity(
        old_name=old_name,
        candidate_name=search_product.name,
        compatibility_product=compatibility_product,
    )

    (
        critical_identity_mismatch,
        critical_identity_reasons,
    ) = has_critical_identity_mismatch(
        old_name=old_name,
        candidate_name=search_product.name,
    )

    score = 0.0

    # --------------------------------------------------------
    # Title similarity
    # --------------------------------------------------------

    score += similarity * 0.50

    reasons.append(f"title similarity={similarity:.3f}")

    # --------------------------------------------------------
    # Manufacturer
    # --------------------------------------------------------

    if manufacturer_match:
        score += 0.15

        reasons.append("manufacturer match")

    elif old_manufacturer:
        reasons.append("manufacturer not confirmed")

    # --------------------------------------------------------
    # Device model overlap
    # --------------------------------------------------------

    if model_overlap > 0:
        score += model_overlap * 0.15

        reasons.append(f"device model overlap={model_overlap:.2f}")

    elif old_model:
        score -= 0.25

        reasons.append("device model not confirmed")

    # --------------------------------------------------------
    # Region / voltage
    # --------------------------------------------------------

    if regional_match is True:
        score += 0.10

        reasons.append("region/voltage match")

    elif regional_match is False:
        score -= 0.25

        reasons.append("region/voltage mismatch")

    # --------------------------------------------------------
    # Pack quantity
    # --------------------------------------------------------

    if pack_match is True:
        score += 0.08

        reasons.append("pack quantity match")

    elif pack_match is False:
        score -= 0.30

        reasons.append("pack quantity mismatch")

    # --------------------------------------------------------
    # Packaging type
    # --------------------------------------------------------

    if packaging_type_match is True:
        score += 0.05

        reasons.append("packaging type match")

    elif packaging_type_match is False:
        score -= 0.30

        reasons.append("packaging type mismatch")

    # --------------------------------------------------------
    # Color
    # --------------------------------------------------------

    if color_match is True:
        score += 0.05

        reasons.append("color match")

    elif color_match is False:
        score -= 0.12

        reasons.append("color mismatch")

    # --------------------------------------------------------
    # Grade / condition
    # --------------------------------------------------------

    if grade_match is True:
        score += 0.07

        reasons.append("grade match")

    elif grade_match is False:
        score -= 0.20

        reasons.append("grade mismatch")

    # --------------------------------------------------------
    # Quality / sourcing tier
    # --------------------------------------------------------

    if quality_tier_match is True:
        score += 0.08

        reasons.append("product quality tier match")

    elif quality_tier_match is False:
        score -= 0.30

        reasons.append("product quality tier mismatch")

    # --------------------------------------------------------
    # Exact device identity
    # --------------------------------------------------------

    if compatibility_product:
        reasons.append("compatibility product: expanded device support allowed")

    elif exact_device_match is True:
        score += 0.12

        reasons.append("exact device identity match")

    elif exact_device_match is False:
        score -= 0.45

        reasons.append("exact device identity mismatch")

    # --------------------------------------------------------
    # Critical identity mismatches
    # --------------------------------------------------------

    if critical_identity_mismatch:
        score -= 0.60

        reasons.extend(critical_identity_reasons)

    # --------------------------------------------------------
    # Detailed supplier status
    # --------------------------------------------------------

    if detailed_product is not None:
        if detailed_product.end_of_life is False:
            score += 0.03

            reasons.append("candidate is active / not EOL")

        elif detailed_product.end_of_life is True:
            reasons.append("candidate is end of life")

        if detailed_product.is_saleable is True:
            score += 0.02

            reasons.append("candidate is saleable")

        elif detailed_product.is_saleable is False:
            reasons.append("candidate is not saleable")

    # --------------------------------------------------------
    # Clamp final score
    # --------------------------------------------------------

    score = max(
        0.0,
        min(
            score,
            1.0,
        ),
    )

    return (
        score,
        similarity,
        manufacturer_match,
        model_overlap,
        regional_match,
        pack_match,
        packaging_type_match,
        color_match,
        grade_match,
        quality_tier_match,
        exact_device_match,
        compatibility_product,
        reasons,
    )


def classify_outcome(
    candidates: list[CandidateResult],
) -> str:
    """
    Classify the best candidate conservatively.

    recovered_same_sku
        The original supplier SKU is available again.

    strong_candidate
        High-confidence replacement with no material incompatibility.

    manual_review
        Plausible replacement that includes a material change requiring
        human approval.

    multiple_candidates
        More than one similarly strong candidate exists.

    weak_candidate
        Some useful similarity exists, but confidence is limited.

    no_candidate
        Nothing sufficiently reliable was found.
    """

    if not candidates:
        return "no_candidate"

    sorted_candidates = sorted(
        candidates,
        key=lambda item: item.score,
        reverse=True,
    )

    best = sorted_candidates[0]

    # Model-specific replacement parts require an exact model match
    # before they may be classified as a strong replacement.
    #
    # A partial 0.80 model overlap can represent materially different
    # devices such as:
    #
    # Xperia X  -> Xperia XA1
    # Xperia XZ -> Xperia XZ1
    # iPhone Pro -> iPhone Pro Max
    #
    # Compatibility tools are allowed to cover expanded device ranges.

    partial_device_match = not best.compatibility_product and best.model_overlap < 1.0

    if best.score < MIN_VIABLE_SCORE:
        return "no_candidate"

    # Material differences must never be auto-approved as a strong
    # replacement even when the overall similarity score is high.
    material_mismatch = (
        partial_device_match
        or best.exact_device_match is False
        or best.pack_match is False
        or best.packaging_type_match is False
        or best.grade_match is False
        or best.quality_tier_match is False
        or best.region_voltage_match is False
        or best.color_match is False
    )

    if material_mismatch:
        if best.score >= MIN_POSSIBLE_SCORE:
            return "manual_review"

        if best.score >= MIN_VIABLE_SCORE:
            return "weak_candidate"

        return "no_candidate"

    if best.score < MIN_POSSIBLE_SCORE:
        return "weak_candidate"

    if best.score < MIN_STRONG_SCORE:
        return "manual_review"

    if len(sorted_candidates) == 1:
        return "strong_candidate"

    second = sorted_candidates[1]

    if best.score - second.score >= 0.10:
        return "strong_candidate"

    return "multiple_candidates"


# ============================================================
# Search helpers
# ============================================================


def collect_search_candidates(
    *,
    client: MobileSentrixClient,
    queries: list[str],
) -> dict[str, MobileSentrixProduct]:
    """
    Run multiple search variants and deduplicate candidates by supplier
    product ID, falling back to SKU when necessary.
    """

    candidates: dict[
        str,
        MobileSentrixProduct,
    ] = {}

    for query in queries:
        print(
            "  Search query:",
            query,
        )

        try:
            result = client.search_products(
                query=query,
                max_results=SEARCH_MAX_RESULTS,
                start_index=0,
            )

        except MobileSentrixApiError as exc:
            print(
                "  Search API error:",
                exc,
            )

            continue

        data = result.get("data")

        if not isinstance(
            data,
            dict,
        ):
            continue

        raw_items = data.get(
            "items",
            [],
        )

        if not isinstance(
            raw_items,
            list,
        ):
            continue

        for raw_item in raw_items:
            if not isinstance(
                raw_item,
                dict,
            ):
                continue

            product = MobileSentrixProduct.from_api_item(raw_item)

            key = product.supplier_product_id or product.supplier_sku

            if not key:
                continue

            candidates[str(key)] = product

        if REQUEST_DELAY_SECONDS > 0:
            time.sleep(REQUEST_DELAY_SECONDS)

    return candidates


def get_workbook_row_data(
    *,
    sync: MobileSentrixWorkbookSyncService,
    row_number: int,
) -> dict[str, object]:
    """
    Read one catalog row from the configured Mobile Sentrix workbook.

    This function is read-only and does not modify the workbook.
    """

    keep_vba = sync.workbook_path.suffix.lower() == ".xlsm"

    workbook = load_workbook(
        sync.workbook_path,
        read_only=True,
        data_only=True,
        keep_vba=keep_vba,
    )

    try:
        if workbook_sync.SHEET_NAME not in workbook.sheetnames:
            raise ValueError("Worksheet not found: " f"{workbook_sync.SHEET_NAME}")

        worksheet = workbook[workbook_sync.SHEET_NAME]

        headers: dict[str, int] = {}

        for column in range(
            1,
            worksheet.max_column + 1,
        ):
            value = worksheet.cell(
                1,
                column,
            ).value

            if value is None:
                continue

            header = str(value).strip()

            if header:
                headers[header] = column

        values: dict[str, object] = {}

        for header, column in headers.items():
            values[header] = worksheet.cell(
                row_number,
                column,
            ).value

        return values

    finally:
        workbook.close()


# ============================================================
# Investigation
# ============================================================


def investigate_item(
    *,
    client: MobileSentrixClient,
    row_number: int,
    old_sku: str,
    row_data: dict[str, object],
) -> InvestigationResult:
    old_name = safe_string(row_data.get("Product Name"))

    old_manufacturer = safe_string(row_data.get("Manufacturer"))

    old_model = safe_string(row_data.get("Device Model"))

    old_category = safe_string(row_data.get("Part Category"))

    old_unit_cost = safe_string(row_data.get("Unit Cost"))

    if not old_name:
        return InvestigationResult(
            workbook_row=row_number,
            old_sku=old_sku,
            old_product_name=old_name,
            old_manufacturer=old_manufacturer,
            old_device_model=old_model,
            old_category=old_category,
            old_unit_cost=old_unit_cost,
            search_queries=[],
            outcome="manual_review",
            selected_candidate=None,
            candidates=[],
            error=("Workbook row has no Product Name."),
        )

    queries = generate_search_queries(
        product_name=old_name,
        manufacturer=old_manufacturer,
    )

    search_candidates = collect_search_candidates(
        client=client,
        queries=queries,
    )

    products = list(search_candidates.values())

    products.sort(
        key=lambda product: (
            title_similarity(
                old_name,
                product.name,
            )
        ),
        reverse=True,
    )

    products = products[:MAX_DETAILED_CANDIDATES]

    candidates: list[CandidateResult] = []

    for search_product in products:
        detailed_product: MobileSentrixDetailedProduct | None = None

        if search_product.supplier_product_id:
            try:
                raw_detailed = client.get_product(
                    product_id=(search_product.supplier_product_id),
                )

                detailed_product = MobileSentrixDetailedProduct.from_api_item(
                    raw_detailed
                )

            except (
                MobileSentrixApiError,
                ValueError,
                TypeError,
            ) as exc:
                print(
                    "  Detailed product lookup failed:",
                    search_product.supplier_product_id,
                    type(exc).__name__,
                    exc,
                )

        (
            score,
            similarity,
            manufacturer_match,
            model_overlap,
            regional_match,
            pack_match,
            packaging_type_match,
            color_match,
            grade_match,
            quality_tier_match,
            exact_device_match,
            compatibility_product,
            reasons,
        ) = score_candidate(
            old_name=old_name,
            old_manufacturer=old_manufacturer,
            old_model=old_model,
            old_category=old_category,
            search_product=search_product,
            detailed_product=detailed_product,
        )

        candidates.append(
            CandidateResult(
                product_id=(
                    search_product
                    .supplier_product_id
                ),
                sku=(
                    search_product
                    .supplier_sku
                ),
                title=(
                    search_product.name
                ),
                search_price=(
                    str(
                        search_product
                        .unit_cost
                    )
                    if search_product
                    .unit_cost
                    is not None
                    else None
                ),
                search_in_stock=(
                    search_product
                    .in_stock
                ),
                title_similarity=round(
                    similarity,
                    4,
                ),
                manufacturer_match=(
                    manufacturer_match
                ),
                model_overlap=round(
                    model_overlap,
                    4,
                ),
                region_voltage_match=(
                    regional_match
                ),
                pack_match=(
                    pack_match
                ),
                packaging_type_match=(
                    packaging_type_match
                ),
                color_match=(
                    color_match
                ),
                grade_match=(
                    grade_match
                ),
                quality_tier_match=(
                    quality_tier_match
                ),
                exact_device_match=(
                    exact_device_match
                ),
                compatibility_product=(
                    compatibility_product
                ),
                score=round(
                    score,
                    4,
                ),
                reasons=reasons,
                detailed_product=(
                    detailed_product
                    .to_api_dict()
                    if detailed_product
                    is not None
                    else None
                ),
            )
        )
        if REQUEST_DELAY_SECONDS > 0:
            time.sleep(REQUEST_DELAY_SECONDS)

    candidates.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    selected_candidate = candidates[0] if candidates else None

    if (
        selected_candidate is not None
        and selected_candidate.sku is not None
        and normalize_text(selected_candidate.sku) == normalize_text(old_sku)
    ):
        outcome = "recovered_same_sku"

    else:
        outcome = classify_outcome(candidates)

    return InvestigationResult(
        workbook_row=row_number,
        old_sku=old_sku,
        old_product_name=old_name,
        old_manufacturer=old_manufacturer,
        old_device_model=old_model,
        old_category=old_category,
        old_unit_cost=old_unit_cost,
        search_queries=queries,
        outcome=outcome,
        selected_candidate=(selected_candidate),
        candidates=candidates,
        error=None,
    )


# ============================================================
# Main runner
# ============================================================


def main() -> int:
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 72)
    print("Mobile Sentrix Unmatched SKU Investigator")
    print("=" * 72)

    sync = MobileSentrixWorkbookSyncService()

    client = MobileSentrixClient()

    checkpoint = sync.get_sync_checkpoint()

    retry_items = checkpoint.get(
        "retry_items",
        [],
    )

    if not isinstance(
        retry_items,
        list,
    ):
        print("Checkpoint retry_items is invalid.")

        return 1

    unmatched_items = [
        item
        for item in retry_items
        if (
            isinstance(
                item,
                dict,
            )
            and str(
                item.get(
                    "status",
                    "",
                )
            )
            .strip()
            .lower()
            == "unmatched"
        )
    ]

    print(
        "Workbook:",
        sync.workbook_path,
    )

    print(
        "Total unmatched records:",
        len(unmatched_items),
    )

    print(
        "Maximum investigated this run:",
        MAX_UNMATCHED_ITEMS,
    )

    print(
        "Report:",
        REPORT_PATH,
    )

    selected_items = unmatched_items[:MAX_UNMATCHED_ITEMS]

    results: list[InvestigationResult] = []

    for index, item in enumerate(
        selected_items,
        start=1,
    ):
        row_number_raw = item.get("row")

        sku_raw = item.get("sku")

        try:
            row_number = int(str(row_number_raw))

        except (
            ValueError,
            TypeError,
        ):
            continue

        sku = str(sku_raw or "").strip()

        if not sku:
            continue

        print()
        print("-" * 72)

        print(f"Investigating " f"{index}/" f"{len(selected_items)}")

        print(
            "Workbook row:",
            row_number,
        )

        print(
            "Old SKU:",
            sku,
        )

        try:
            row_data = get_workbook_row_data(
                sync=sync,
                row_number=row_number,
            )

            result = investigate_item(
                client=client,
                row_number=row_number,
                old_sku=sku,
                row_data=row_data,
            )

        except Exception as exc:
            traceback.print_exc()

            result = InvestigationResult(
                workbook_row=row_number,
                old_sku=sku,
                old_product_name=None,
                old_manufacturer=None,
                old_device_model=None,
                old_category=None,
                old_unit_cost=None,
                search_queries=[],
                outcome="api_error",
                selected_candidate=None,
                candidates=[],
                error=(f"{type(exc).__name__}: " f"{exc}"),
            )

        results.append(result)

        print(
            "Product:",
            result.old_product_name,
        )

        print(
            "Outcome:",
            result.outcome,
        )

        if result.selected_candidate is not None:
            candidate = result.selected_candidate

            print(
                "Best candidate SKU:",
                candidate.sku,
            )

            print(
                "Best candidate product ID:",
                candidate.product_id,
            )

            print(
                "Best candidate score:",
                candidate.score,
            )

            print(
                "Best candidate title:",
                candidate.title,
            )

            print("Evidence:")

            for reason in candidate.reasons:
                print(
                    "  -",
                    reason,
                )

    outcome_counts: dict[
        str,
        int,
    ] = {}

    for result in results:
        outcome_counts[result.outcome] = (
            outcome_counts.get(
                result.outcome,
                0,
            )
            + 1
        )

    report = {
        "generated_at": (datetime.now(UTC).isoformat()),
        "workbook": str(sync.workbook_path),
        "checkpoint_cycle_complete": (checkpoint.get("cycle_complete")),
        "total_unmatched_records": (len(unmatched_items)),
        "investigated_this_run": (len(results)),
        "configuration": {
            "max_unmatched_items": (MAX_UNMATCHED_ITEMS),
            "search_max_results": (SEARCH_MAX_RESULTS),
            "min_strong_score": (MIN_STRONG_SCORE),
            "min_possible_score": (MIN_POSSIBLE_SCORE),
            "max_detailed_candidates": (MAX_DETAILED_CANDIDATES),
            "max_search_queries_per_item": (MAX_SEARCH_QUERIES_PER_ITEM),
        },
        "outcome_counts": (outcome_counts),
        "results": [asdict(result) for result in results],
    }

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("Investigation complete")
    print("=" * 72)

    print(
        "Investigated:",
        len(results),
    )

    print(
        "Outcome counts:",
        outcome_counts,
    )

    print(
        "Report:",
        REPORT_PATH,
    )

    print()
    print("No workbook or checkpoint " "changes were made.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
