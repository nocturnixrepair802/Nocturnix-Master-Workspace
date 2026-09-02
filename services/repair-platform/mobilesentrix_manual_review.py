from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

REPORT_DIR = BASE_DIR / "Data" / "reports"

SOURCE_REPORT_PATH = REPORT_DIR / "mobilesentrix_unmatched_20260901T150820Z.json"

RUN_TIMESTAMP = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

OUTPUT_REPORT_PATH = REPORT_DIR / f"mobilesentrix_manual_review_{RUN_TIMESTAMP}.json"

TARGET_OUTCOME = "manual_review"


# ============================================================
# Models
# ============================================================


@dataclass(slots=True)
class ManualReviewItem:
    workbook_row: int | None

    old_sku: str | None
    old_product_name: str | None
    old_manufacturer: str | None
    old_device_model: str | None
    old_category: str | None
    old_unit_cost: str | None

    candidate_sku: str | None
    candidate_product_id: str | None
    candidate_title: str | None
    candidate_score: float | None

    candidate_price: str | None
    price_difference: str | None
    price_change_percent: str | None

    search_in_stock: bool | None

    detailed_in_stock: bool | None
    detailed_stock_quantity: int | None
    detailed_saleable: bool | None
    detailed_end_of_life: bool | None

    manufacturer_match: bool | None
    model_overlap: float | None

    region_voltage_match: bool | None
    pack_match: bool | None
    packaging_type_match: bool | None
    color_match: bool | None
    grade_match: bool | None

    quality_tier_match: bool | None
    exact_device_match: bool | None
    compatibility_product: bool | None

    evidence: list[str]


# ============================================================
# Helpers
# ============================================================


def load_json_object(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Source report not found: {path}")

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        result = json.load(file)

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError("Source report must contain a JSON object.")

    return result


def to_string(
    value: object,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def to_float(
    value: object,
) -> float | None:
    if value is None:
        return None

    if isinstance(
        value,
        (
            int,
            float,
            str,
        ),
    ):
        try:
            return float(value)

        except ValueError:
            return None

    return None


def to_int(
    value: object,
) -> int | None:
    if value is None:
        return None

    try:
        return int(str(value))

    except (
        TypeError,
        ValueError,
    ):
        return None


def to_bool(
    value: object,
) -> bool | None:
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        if value == 1:
            return True

        if value == 0:
            return False

    text = str(value).strip().lower()

    if text in {
        "1",
        "true",
        "yes",
    }:
        return True

    if text in {
        "0",
        "false",
        "no",
    }:
        return False

    return None


def to_decimal(
    value: object,
) -> Decimal | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    text = text.replace("$", "").replace(",", "").strip()

    try:
        return Decimal(text)

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return None


def calculate_price_difference(
    *,
    old_cost: object,
    new_cost: object,
) -> tuple[
    str | None,
    str | None,
]:
    old_decimal = to_decimal(old_cost)

    new_decimal = to_decimal(new_cost)

    if old_decimal is None or new_decimal is None:
        return (
            None,
            None,
        )

    difference = new_decimal - old_decimal

    if old_decimal == 0:
        percentage = None

    else:
        percentage = difference / old_decimal * Decimal("100")

    return (
        format(
            difference,
            "f",
        ),
        (f"{percentage:.2f}" if percentage is not None else None),
    )


def as_dict(
    value: object,
) -> dict[str, Any]:
    if not isinstance(
        value,
        dict,
    ):
        return {}

    return {str(key): item for key, item in value.items()}


def as_list(
    value: object,
) -> list[Any]:
    if not isinstance(
        value,
        list,
    ):
        return []

    return value


# ============================================================
# Review extraction
# ============================================================


def build_review_item(
    result: dict[str, Any],
) -> ManualReviewItem | None:
    candidate = as_dict(result.get("selected_candidate"))

    if not candidate:
        return None

    detailed = as_dict(candidate.get("detailed_product"))

    old_unit_cost = result.get("old_unit_cost")

    candidate_price = (
        detailed.get("customer_price")
        if detailed.get("customer_price") is not None
        else candidate.get("search_price")
    )

    (
        price_difference,
        price_change_percent,
    ) = calculate_price_difference(
        old_cost=old_unit_cost,
        new_cost=candidate_price,
    )

    evidence = [str(item) for item in as_list(candidate.get("reasons"))]

    return ManualReviewItem(
        workbook_row=to_int(result.get("workbook_row")),
        old_sku=to_string(result.get("old_sku")),
        old_product_name=to_string(result.get("old_product_name")),
        old_manufacturer=to_string(result.get("old_manufacturer")),
        old_device_model=to_string(result.get("old_device_model")),
        old_category=to_string(result.get("old_category")),
        old_unit_cost=to_string(old_unit_cost),
        candidate_sku=to_string(candidate.get("sku")),
        candidate_product_id=to_string(candidate.get("product_id")),
        candidate_title=to_string(candidate.get("title")),
        candidate_score=to_float(candidate.get("score")),
        candidate_price=to_string(candidate_price),
        price_difference=(price_difference),
        price_change_percent=(price_change_percent),
        search_in_stock=to_bool(candidate.get("search_in_stock")),
        detailed_in_stock=to_bool(detailed.get("is_in_stock")),
        detailed_stock_quantity=to_int(detailed.get("in_stock_qty")),
        detailed_saleable=to_bool(detailed.get("is_saleable")),
        detailed_end_of_life=to_bool(detailed.get("end_of_life")),
        manufacturer_match=to_bool(candidate.get("manufacturer_match")),
        model_overlap=to_float(candidate.get("model_overlap")),
        region_voltage_match=to_bool(candidate.get("region_voltage_match")),
        pack_match=to_bool(candidate.get("pack_match")),
        packaging_type_match=to_bool(candidate.get("packaging_type_match")),
        color_match=to_bool(candidate.get("color_match")),
        grade_match=to_bool(candidate.get("grade_match")),
        quality_tier_match=to_bool(candidate.get("quality_tier_match")),
        exact_device_match=to_bool(candidate.get("exact_device_match")),
        compatibility_product=to_bool(candidate.get("compatibility_product")),
        evidence=evidence,
    )


# ============================================================
# Terminal output
# ============================================================


def print_review_item(
    *,
    index: int,
    total: int,
    item: ManualReviewItem,
) -> None:
    print()
    print("=" * 72)

    print(f"Manual Review " f"{index}/{total}")

    print("=" * 72)

    print(
        "Workbook row:",
        item.workbook_row,
    )

    print(
        "Old SKU:",
        item.old_sku,
    )

    print(
        "Candidate SKU:",
        item.candidate_sku,
    )

    print(
        "Candidate product ID:",
        item.candidate_product_id,
    )

    print(
        "Score:",
        item.candidate_score,
    )

    print()

    print("OLD PRODUCT")

    print("-----------")

    print(item.old_product_name)

    print(
        "Manufacturer:",
        item.old_manufacturer,
    )

    print(
        "Device:",
        item.old_device_model,
    )

    print(
        "Category:",
        item.old_category,
    )

    print(
        "Old cost:",
        item.old_unit_cost,
    )

    print()

    print("CANDIDATE PRODUCT")

    print("-----------------")

    print(item.candidate_title)

    print(
        "Current price:",
        item.candidate_price,
    )

    print(
        "Price difference:",
        item.price_difference,
    )

    if item.price_change_percent is not None:
        print(
            "Price change:",
            f"{item.price_change_percent}%",
        )

    print(
        "In stock:",
        item.detailed_in_stock,
    )

    print(
        "Stock quantity:",
        item.detailed_stock_quantity,
    )

    print(
        "Saleable:",
        item.detailed_saleable,
    )

    print(
        "End of life:",
        item.detailed_end_of_life,
    )

    print()

    print("MATCH FLAGS")

    print("-----------")

    print(
        "Manufacturer:",
        item.manufacturer_match,
    )

    print(
        "Model overlap:",
        item.model_overlap,
    )

    print(
        "Exact device:",
        item.exact_device_match,
    )

    print(
        "Compatibility product:",
        item.compatibility_product,
    )

    print(
        "Region / voltage:",
        item.region_voltage_match,
    )

    print(
        "Pack quantity:",
        item.pack_match,
    )

    print(
        "Packaging:",
        item.packaging_type_match,
    )

    print(
        "Color:",
        item.color_match,
    )

    print(
        "Grade:",
        item.grade_match,
    )

    print(
        "Quality tier:",
        item.quality_tier_match,
    )

    print()

    print("EVIDENCE")

    print("--------")

    for reason in item.evidence:
        print(
            "  -",
            reason,
        )


# ============================================================
# Main
# ============================================================


def main() -> int:
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 72)

    print("Mobile Sentrix Manual Replacement Review")

    print("=" * 72)

    print(
        "Source report:",
        SOURCE_REPORT_PATH,
    )

    source = load_json_object(SOURCE_REPORT_PATH)

    raw_results = source.get(
        "results",
        [],
    )

    if not isinstance(
        raw_results,
        list,
    ):
        raise ValueError("Source report results must be a list.")

    review_items: list[ManualReviewItem] = []

    for raw_result in raw_results:
        if not isinstance(
            raw_result,
            dict,
        ):
            continue

        outcome = (
            str(
                raw_result.get(
                    "outcome",
                    "",
                )
            )
            .strip()
            .lower()
        )

        if outcome != TARGET_OUTCOME:
            continue

        normalized_result = {str(key): value for key, value in raw_result.items()}

        item = build_review_item(normalized_result)

        if item is not None:
            review_items.append(item)

    review_items.sort(
        key=lambda item: (
            item.candidate_score if item.candidate_score is not None else 0.0
        ),
        reverse=True,
    )

    print(
        "Manual-review candidates found:",
        len(review_items),
    )

    for index, item in enumerate(
        review_items,
        start=1,
    ):
        print_review_item(
            index=index,
            total=len(review_items),
            item=item,
        )

    report = {
        "generated_at": (datetime.now(UTC).isoformat()),
        "source_report": str(SOURCE_REPORT_PATH),
        "manual_review_count": (len(review_items)),
        "review_items": [asdict(item) for item in review_items],
    }

    OUTPUT_REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)

    print("Manual review report complete")

    print("=" * 72)

    print(
        "Candidates reviewed:",
        len(review_items),
    )

    print(
        "Report:",
        OUTPUT_REPORT_PATH,
    )

    print()

    print("No workbook or checkpoint changes were made.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
