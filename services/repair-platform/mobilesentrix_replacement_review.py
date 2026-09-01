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

OUTPUT_REPORT_PATH = (
    REPORT_DIR / f"mobilesentrix_replacement_review_{RUN_TIMESTAMP}.json"
)

TARGET_OUTCOME = "strong_candidate"


# ============================================================
# Models
# ============================================================


@dataclass(slots=True)
class ReplacementReviewItem:
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
    detailed_end_of_life: bool | None
    detailed_saleable: bool | None

    manufacturer_match: bool | None
    model_overlap: float | None

    region_voltage_match: bool | None
    pack_match: bool | None
    packaging_type_match: bool | None
    color_match: bool | None
    grade_match: bool | None

    evidence: list[str]


# ============================================================
# Utility functions
# ============================================================


def load_json_object(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {path}")

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        result = json.load(file)

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError("Investigation report must contain a JSON object.")

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
        bool,
    ):
        return float(value)

    if isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        return float(value)

    try:
        return float(str(value).strip())

    except (
        ValueError,
        TypeError,
    ):
        return None


def to_int(
    value: object,
) -> int | None:
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return int(value)

    if isinstance(
        value,
        int,
    ):
        return value

    try:
        return int(str(value).strip())

    except (
        ValueError,
        TypeError,
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
        "true",
        "1",
        "yes",
    }:
        return True

    if text in {
        "false",
        "0",
        "no",
    }:
        return False

    return None


def to_decimal(
    value: object,
) -> Decimal | None:
    if value is None:
        return None

    if isinstance(
        value,
        Decimal,
    ):
        return value

    text = str(value).strip()

    if not text:
        return None

    text = text.replace("$", "").replace(",", "").strip()

    try:
        return Decimal(text)

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return None


def decimal_string(
    value: Decimal | None,
) -> str | None:
    if value is None:
        return None

    return format(
        value,
        "f",
    )


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
        percent = None

    else:
        percent = difference / old_decimal * Decimal("100")

    return (
        decimal_string(difference),
        (f"{percent:.2f}" if percent is not None else None),
    )


def get_dict(
    value: object,
) -> dict[str, Any]:
    if not isinstance(
        value,
        dict,
    ):
        return {}

    return {str(key): item for key, item in value.items()}


def get_list(
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
) -> ReplacementReviewItem | None:
    candidate = get_dict(result.get("selected_candidate"))

    if not candidate:
        return None

    detailed = get_dict(candidate.get("detailed_product"))

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

    evidence_raw = get_list(candidate.get("reasons"))

    evidence = [str(item) for item in evidence_raw]

    return ReplacementReviewItem(
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
        detailed_end_of_life=to_bool(detailed.get("end_of_life")),
        detailed_saleable=to_bool(detailed.get("is_saleable")),
        manufacturer_match=to_bool(candidate.get("manufacturer_match")),
        model_overlap=to_float(candidate.get("model_overlap")),
        region_voltage_match=to_bool(candidate.get("region_voltage_match")),
        pack_match=to_bool(candidate.get("pack_match")),
        packaging_type_match=to_bool(candidate.get("packaging_type_match")),
        color_match=to_bool(candidate.get("color_match")),
        grade_match=to_bool(candidate.get("grade_match")),
        evidence=evidence,
    )


# ============================================================
# Terminal output
# ============================================================


def print_review_item(
    *,
    index: int,
    total: int,
    item: ReplacementReviewItem,
) -> None:
    print()
    print("=" * 72)

    print(f"Strong Candidate " f"{index}/{total}")

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
        "New SKU:",
        item.candidate_sku,
    )

    print(
        "Mobile Sentrix product ID:",
        item.candidate_product_id,
    )

    print()

    print("OLD PRODUCT")

    print("-----------")

    print(
        "Name:",
        item.old_product_name,
    )

    print(
        "Manufacturer:",
        item.old_manufacturer,
    )

    print(
        "Device model:",
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

    print("PROPOSED CURRENT PRODUCT")

    print("------------------------")

    print(
        "Name:",
        item.candidate_title,
    )

    print(
        "Confidence score:",
        item.candidate_score,
    )

    print(
        "Current Mobile Sentrix price:",
        item.candidate_price,
    )

    print(
        "Price difference:",
        item.price_difference,
    )

    if item.price_change_percent is not None:
        print(
            "Price change percent:",
            f"{item.price_change_percent}%",
        )

    print()

    print("SUPPLIER STATUS")

    print("---------------")

    print(
        "Search says in stock:",
        item.search_in_stock,
    )

    print(
        "Detailed in stock:",
        item.detailed_in_stock,
    )

    print(
        "Detailed stock quantity:",
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

    print("MATCH EVIDENCE")

    print("--------------")

    print(
        "Manufacturer match:",
        item.manufacturer_match,
    )

    print(
        "Device model overlap:",
        item.model_overlap,
    )

    print(
        "Region / voltage match:",
        item.region_voltage_match,
    )

    print(
        "Pack quantity match:",
        item.pack_match,
    )

    print(
        "Packaging type match:",
        item.packaging_type_match,
    )

    print(
        "Color match:",
        item.color_match,
    )

    print(
        "Grade match:",
        item.grade_match,
    )

    print()

    print("Evidence:")

    if item.evidence:
        for evidence in item.evidence:
            print(
                "  -",
                evidence,
            )

    else:
        print("  No evidence details were recorded.")


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

    print("Mobile Sentrix Strong Replacement Review")

    print("=" * 72)

    print(
        "Source report:",
        SOURCE_REPORT_PATH,
    )

    investigation = load_json_object(SOURCE_REPORT_PATH)

    raw_results = investigation.get(
        "results",
        [],
    )

    if not isinstance(
        raw_results,
        list,
    ):
        raise ValueError("Investigation report results must be a list.")

    strong_results: list[dict[str, Any]] = []

    for raw_result in raw_results:
        if not isinstance(
            raw_result,
            dict,
        ):
            continue

        result = {str(key): value for key, value in raw_result.items()}

        outcome = (
            str(
                result.get(
                    "outcome",
                    "",
                )
            )
            .strip()
            .lower()
        )

        if outcome == TARGET_OUTCOME:
            strong_results.append(result)

    review_items: list[ReplacementReviewItem] = []

    for result in strong_results:
        item = build_review_item(result)

        if item is not None:
            review_items.append(item)

    review_items.sort(
        key=lambda item: (
            item.candidate_score if item.candidate_score is not None else 0.0
        ),
        reverse=True,
    )

    print(
        "Strong candidates found:",
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

    output = {
        "generated_at": (datetime.now(UTC).isoformat()),
        "source_report": str(SOURCE_REPORT_PATH),
        "source_total_unmatched_records": (
            investigation.get("total_unmatched_records")
        ),
        "source_investigated_records": (investigation.get("investigated_this_run")),
        "target_outcome": (TARGET_OUTCOME),
        "strong_candidate_count": (len(review_items)),
        "review_items": [asdict(item) for item in review_items],
    }

    OUTPUT_REPORT_PATH.write_text(
        json.dumps(
            output,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)

    print("Replacement review complete")

    print("=" * 72)

    print(
        "Strong candidates reviewed:",
        len(review_items),
    )

    print(
        "Review report:",
        OUTPUT_REPORT_PATH,
    )

    print()

    print("No workbook or checkpoint changes were made.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
