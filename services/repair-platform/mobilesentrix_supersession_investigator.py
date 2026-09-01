from __future__ import annotations

import json
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from integrations.mobilesentrix import (
    MobileSentrixWorkbookSyncService,
)
from integrations.mobilesentrix.client import (
    MobileSentrixClient,
)

# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

REPORT_DIR = BASE_DIR / "Data" / "reports"

SOURCE_REPORT_PATH = REPORT_DIR / "mobilesentrix_unmatched_20260901T150820Z.json"

RUN_TIMESTAMP = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

OUTPUT_REPORT_PATH = REPORT_DIR / f"mobilesentrix_supersession_" f"{RUN_TIMESTAMP}.json"

REQUEST_DELAY_SECONDS = 0.20

SEARCH_MAX_RESULTS = 25

# First run only 50 so we can inspect behavior before
# querying all remaining unresolved records.
MAX_ITEMS = 270


# ============================================================
# Helpers
# ============================================================


def normalize_sku(
    value: object,
) -> str:
    return str(value or "").strip()


def normalize_text(
    value: object,
) -> str:
    return " ".join(str(value or "").strip().lower().split())


def safe_string(
    value: object,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def safe_int(
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
        raise ValueError("Source report must contain " "a JSON object.")

    return result


def get_search_items(
    response: dict[str, object],
) -> list[dict[str, Any]]:
    data = response.get("data")

    if not isinstance(
        data,
        dict,
    ):
        return []

    raw_items = data.get("items")

    if not isinstance(
        raw_items,
        list,
    ):
        return []

    return [
        item
        for item in raw_items
        if isinstance(
            item,
            dict,
        )
    ]


def search_item_sku(
    item: dict[str, Any],
) -> str:
    return normalize_sku(item.get("product_code") or item.get("sku"))


def search_item_product_id(
    item: dict[str, Any],
) -> str | None:
    value = item.get("product_id") or item.get("entity_id")

    return safe_string(value)


def search_item_title(
    item: dict[str, Any],
) -> str | None:
    return safe_string(item.get("title") or item.get("name"))


def find_exact_sku(
    *,
    items: list[dict[str, Any]],
    sku: str,
) -> dict[str, Any] | None:
    target = normalize_sku(sku)

    for item in items:
        if search_item_sku(item) == target:
            return item

    return None


def extract_explicit_new_sku(
    product: dict[str, Any],
) -> str | None:
    """
    Return an explicit Mobile Sentrix replacement SKU
    only when the detailed product response actually
    provides one.
    """

    new_sku = normalize_sku(product.get("new_sku"))

    current_sku = normalize_sku(product.get("sku"))

    if not new_sku:
        return None

    if current_sku and new_sku == current_sku:
        return None

    return new_sku


def extract_related_product(
    product: dict[str, Any],
) -> dict[str, str | None] | None:
    """
    Extract real Mobile Sentrix related-product metadata.

    Empty arrays, empty dictionaries, null values, and string
    representations such as "[]" or "{}" are treated as no
    relationship.

    This function does not infer that a related product is a
    replacement. It only reports actual relationship metadata
    returned by Mobile Sentrix.
    """

    raw_related_id = product.get("related_product_id") or product.get("related_product")

    raw_related_sku = product.get("related_product_sku") or product.get("related_sku")

    def normalize_related_value(
        value: object,
    ) -> str | None:
        if value is None:
            return None

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
                dict,
            ),
        ):
            if not value:
                return None

            # Do not stringify complex relationship structures here.
            # They require separate parsing before they can safely be
            # interpreted as a specific product ID or SKU.
            return None

        text = str(value).strip()

        if not text:
            return None

        if text.lower() in {
            "[]",
            "{}",
            "none",
            "null",
        }:
            return None

        return text

    related_id = normalize_related_value(raw_related_id)

    related_sku = normalize_related_value(raw_related_sku)

    if related_id is None and related_sku is None:
        return None

    return {
        "product_id": related_id,
        "sku": related_sku,
    }


# ============================================================
# Candidate detail helpers
# ============================================================


def get_product_detail(
    *,
    client: MobileSentrixClient,
    product_id: str,
) -> dict[str, Any]:
    result = client.get_product(product_id=product_id)

    if not isinstance(
        result,
        dict,
    ):
        raise RuntimeError("Detailed product response " "was not a JSON object.")

    return {str(key): value for key, value in result.items()}


def summarize_detail(
    product: dict[str, Any],
) -> dict[str, Any]:
    return {
        "entity_id": (product.get("entity_id")),
        "sku": (product.get("sku")),
        "new_sku": (product.get("new_sku")),
        "name": (product.get("name")),
        "customer_price": (product.get("customer_price")),
        "status": (product.get("status")),
        "is_saleable": (product.get("is_saleable")),
        "is_in_stock": (product.get("is_in_stock")),
        "in_stock_qty": (product.get("in_stock_qty")),
        "end_of_life": (product.get("end_of_life")),
        "manufacturer": (product.get("manufacturer")),
        "manufacturer_text": (product.get("manufacturer_text")),
        "model": (product.get("model")),
        "model_text": (product.get("model_text")),
        "category_ids": (product.get("category_ids")),
        "product_url": (product.get("product_url") or product.get("url")),
        "related_product": (extract_related_product(product)),
    }


# ============================================================
# Investigation
# ============================================================


def investigate_record(
    *,
    client: MobileSentrixClient,
    record: dict[str, Any],
) -> dict[str, Any]:
    row = safe_int(record.get("workbook_row"))

    old_sku = normalize_sku(record.get("old_sku"))

    old_name = safe_string(record.get("old_product_name"))

    result: dict[str, Any] = {
        "workbook_row": row,
        "old_sku": old_sku,
        "old_product_name": old_name,
        "original_outcome": (record.get("outcome")),
        "outcome": ("remain_unmatched"),
        "exact_same_sku": None,
        "explicit_new_sku": None,
        "related_product": None,
        "candidate_detail": None,
        "evidence": [],
        "errors": [],
    }

    evidence: list[str] = result["evidence"]

    errors: list[str] = result["errors"]

    if not old_sku:
        result["outcome"] = "invalid_record"

        errors.append("Old SKU is missing.")

        return result

    # --------------------------------------------------------
    # Stage 1:
    # Search the original SKU again.
    # --------------------------------------------------------

    try:
        search_response = client.search_products(
            query=old_sku,
            max_results=(SEARCH_MAX_RESULTS),
            start_index=0,
        )

        search_items = get_search_items(search_response)

    except Exception as exc:
        result["outcome"] = "api_error"

        errors.append(f"SKU search failed: " f"{type(exc).__name__}: {exc}")

        return result

    exact_item = find_exact_sku(
        items=search_items,
        sku=old_sku,
    )

    if exact_item is not None:
        exact_product_id = search_item_product_id(exact_item)

        result["exact_same_sku"] = {
            "sku": (search_item_sku(exact_item)),
            "product_id": (exact_product_id),
            "title": (search_item_title(exact_item)),
        }

        evidence.append("Original SKU returned by " "Mobile Sentrix search.")

        # ----------------------------------------------------
        # If possible, inspect the exact product detail for
        # explicit supplier supersession metadata.
        # ----------------------------------------------------

        if exact_product_id:
            try:
                time.sleep(REQUEST_DELAY_SECONDS)

                exact_detail = get_product_detail(
                    client=client,
                    product_id=(exact_product_id),
                )

                result["candidate_detail"] = summarize_detail(exact_detail)

                explicit_new_sku = extract_explicit_new_sku(exact_detail)

                if explicit_new_sku:
                    result["explicit_new_sku"] = explicit_new_sku

                    evidence.append(
                        "Detailed Mobile Sentrix "
                        "product explicitly provides "
                        f"new_sku={explicit_new_sku}."
                    )

                    result["outcome"] = "supplier_confirmed_replacement"

                    return result

                related = extract_related_product(exact_detail)

                if related is not None:
                    result["related_product"] = related

                    evidence.append(
                        "Detailed Mobile Sentrix "
                        "product contains related-product "
                        "metadata."
                    )

                    result["outcome"] = "supplier_related_candidate"

                    return result

            except Exception as exc:
                errors.append(
                    "Exact product detail failed: " f"{type(exc).__name__}: {exc}"
                )

        result["outcome"] = "recovered_same_sku"

        return result

    # --------------------------------------------------------
    # Stage 2:
    # Search by the old product name.
    #
    # We are NOT declaring these replacements based on title
    # similarity. We are using the search only to locate
    # detailed Mobile Sentrix records that might expose
    # explicit supplier metadata.
    # --------------------------------------------------------

    if not old_name:
        evidence.append(
            "Original SKU was not returned and " "no product name is available."
        )

        return result

    try:
        time.sleep(REQUEST_DELAY_SECONDS)

        name_response = client.search_products(
            query=old_name,
            max_results=(SEARCH_MAX_RESULTS),
            start_index=0,
        )

        name_items = get_search_items(name_response)

    except Exception as exc:
        result["outcome"] = "api_error"

        errors.append("Product-name search failed: " f"{type(exc).__name__}: {exc}")

        return result

    if not name_items:
        evidence.append(
            "No Mobile Sentrix candidates " "returned from product-name search."
        )

        return result

    # --------------------------------------------------------
    # Inspect up to five search results.
    # --------------------------------------------------------

    for candidate in name_items[:5]:
        candidate_id = search_item_product_id(candidate)

        if not candidate_id:
            continue

        try:
            time.sleep(REQUEST_DELAY_SECONDS)

            detail = get_product_detail(
                client=client,
                product_id=(candidate_id),
            )

        except Exception as exc:
            errors.append(
                "Candidate detail failed for "
                f"{candidate_id}: "
                f"{type(exc).__name__}: {exc}"
            )

            continue

        explicit_new_sku = extract_explicit_new_sku(detail)

        if explicit_new_sku:
            result["explicit_new_sku"] = explicit_new_sku

            result["candidate_detail"] = summarize_detail(detail)

            evidence.append(
                "Candidate detailed product "
                "contains explicit "
                f"new_sku={explicit_new_sku}."
            )

            result["outcome"] = "supplier_confirmed_replacement"

            return result

        related = extract_related_product(detail)

        if related is not None:
            result["related_product"] = related

            result["candidate_detail"] = summarize_detail(detail)

            evidence.append(
                "Candidate detailed product " "contains related-product metadata."
            )

            result["outcome"] = "supplier_related_candidate"

            return result

    evidence.append("No explicit Mobile Sentrix supersession " "metadata was found.")

    return result


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

    print("Mobile Sentrix Supplier Supersession Investigator")

    print("=" * 72)

    print(
        "Source report:",
        SOURCE_REPORT_PATH,
    )

    print(
        "Maximum records:",
        MAX_ITEMS,
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

    # --------------------------------------------------------
    # Read the current checkpoint so already-resolved records
    # are excluded.
    # --------------------------------------------------------

    sync = MobileSentrixWorkbookSyncService()

    checkpoint = sync.get_sync_checkpoint()

    retry_items = checkpoint.get(
        "retry_items",
        [],
    )

    if not isinstance(
        retry_items,
        list,
    ):
        raise ValueError("Checkpoint retry_items must be a list.")

    unresolved_keys: set[tuple[int, str]] = set()

    for item in retry_items:
        if not isinstance(
            item,
            dict,
        ):
            continue

        status = normalize_text(item.get("status"))

        if status != "unmatched":
            continue

        row = safe_int(item.get("row"))

        sku = normalize_sku(item.get("sku"))

        if row is not None and sku:
            unresolved_keys.add(
                (
                    row,
                    sku,
                )
            )

    investigation_records: list[dict[str, Any]] = []

    for raw_result in raw_results:
        if not isinstance(
            raw_result,
            dict,
        ):
            continue

        row = safe_int(raw_result.get("workbook_row"))

        sku = normalize_sku(raw_result.get("old_sku"))

        if row is None or not sku:
            continue

        if (
            row,
            sku,
        ) not in unresolved_keys:
            continue

        investigation_records.append(
            {str(key): value for key, value in raw_result.items()}
        )

    investigation_records = investigation_records[:MAX_ITEMS]

    print(
        "Unresolved records selected:",
        len(investigation_records),
    )

    client = MobileSentrixClient()

    results: list[dict[str, Any]] = []

    for index, record in enumerate(
        investigation_records,
        start=1,
    ):
        print()
        print("-" * 72)

        print(f"Investigating " f"{index}/" f"{len(investigation_records)}")

        print(
            "Workbook row:",
            record.get("workbook_row"),
        )

        print(
            "Old SKU:",
            record.get("old_sku"),
        )

        try:
            result = investigate_record(
                client=client,
                record=record,
            )

        except Exception as exc:
            result = {
                "workbook_row": (record.get("workbook_row")),
                "old_sku": (record.get("old_sku")),
                "old_product_name": (record.get("old_product_name")),
                "original_outcome": (record.get("outcome")),
                "outcome": ("api_error"),
                "exact_same_sku": None,
                "explicit_new_sku": None,
                "related_product": None,
                "candidate_detail": None,
                "evidence": [],
                "errors": [f"{type(exc).__name__}: " f"{exc}"],
            }

        results.append(result)

        print(
            "Outcome:",
            result.get("outcome"),
        )

        if result.get("explicit_new_sku"):
            print(
                "Explicit new SKU:",
                result.get("explicit_new_sku"),
            )

        if result.get("related_product"):
            print(
                "Related product:",
                result.get("related_product"),
            )

        if result.get("errors"):
            for error in result["errors"]:
                print(
                    "  ERROR:",
                    error,
                )

        time.sleep(REQUEST_DELAY_SECONDS)

    outcome_counts = Counter(
        str(
            result.get(
                "outcome",
                "unknown",
            )
        )
        for result in results
    )

    report = {
        "generated_at": (datetime.now(UTC).isoformat()),
        "source_report": str(SOURCE_REPORT_PATH),
        "checkpoint_unmatched_count": (len(unresolved_keys)),
        "investigated_count": (len(results)),
        "outcome_counts": dict(outcome_counts),
        "results": results,
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

    print("Supersession investigation complete")

    print("=" * 72)

    print(
        "Investigated:",
        len(results),
    )

    print(
        "Outcome counts:",
        dict(outcome_counts),
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
