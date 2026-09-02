from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from integrations.mobilesentrix import (
    MobileSentrixWorkbookSyncService,
)

# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

REPORT_DIR = BASE_DIR / "Data" / "reports"

SOURCE_REPORT_PATH = REPORT_DIR / "mobilesentrix_supersession_20260901T212521Z.json"

RUN_TIMESTAMP = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

RESOLUTION_REPORT_PATH = (
    REPORT_DIR / f"mobilesentrix_supersession_same_sku_resolution_"
    f"{RUN_TIMESTAMP}.json"
)

TARGET_OUTCOME = "recovered_same_sku"


# ============================================================
# Helpers
# ============================================================


def normalize_sku(
    value: object,
) -> str:
    return str(value or "").strip()


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
        raise ValueError("Source report must contain a JSON object.")

    return result


def find_checkpoint_item(
    *,
    retry_items: list[object],
    row_number: int,
    sku: str,
) -> dict[str, object] | None:
    for raw_item in retry_items:
        if not isinstance(
            raw_item,
            dict,
        ):
            continue

        item_row = safe_int(raw_item.get("row"))

        item_sku = normalize_sku(raw_item.get("sku"))

        if item_row == row_number and item_sku == sku:
            return raw_item

    return None


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

    print("Mobile Sentrix Supersession Same-SKU Resolver")

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

    recovered_results: list[dict[str, Any]] = []

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

        old_sku = normalize_sku(raw_result.get("old_sku"))

        exact_same_sku = raw_result.get("exact_same_sku")

        if not isinstance(
            exact_same_sku,
            dict,
        ):
            continue

        found_sku = normalize_sku(exact_same_sku.get("sku"))

        if not old_sku or not found_sku or old_sku != found_sku:
            continue

        recovered_results.append({str(key): value for key, value in raw_result.items()})

    print(
        "Verified recovered same-SKU records:",
        len(recovered_results),
    )

    if not recovered_results:
        print()
        print("Nothing to resolve.")

        return 0

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

    resolved_at = datetime.now(UTC).isoformat()

    resolved_records: list[dict[str, object]] = []

    skipped_records: list[dict[str, object]] = []

    resolved_count = 0

    for recovered in recovered_results:
        row_number = safe_int(recovered.get("workbook_row"))

        old_sku = normalize_sku(recovered.get("old_sku"))

        exact_same_sku = recovered.get("exact_same_sku")

        if not isinstance(
            exact_same_sku,
            dict,
        ):
            skipped_records.append(
                {
                    "row": row_number,
                    "sku": old_sku,
                    "reason": ("Missing exact_same_sku data."),
                }
            )

            continue

        found_sku = normalize_sku(exact_same_sku.get("sku"))

        product_id = exact_same_sku.get("product_id")

        if row_number is None:
            skipped_records.append(
                {
                    "row": (recovered.get("workbook_row")),
                    "sku": old_sku,
                    "reason": ("Invalid workbook row."),
                }
            )

            continue

        if old_sku != found_sku:
            skipped_records.append(
                {
                    "row": row_number,
                    "sku": old_sku,
                    "found_sku": found_sku,
                    "reason": ("Recovered SKU does not equal old SKU."),
                }
            )

            continue

        checkpoint_item = find_checkpoint_item(
            retry_items=retry_items,
            row_number=row_number,
            sku=old_sku,
        )

        if checkpoint_item is None:
            skipped_records.append(
                {
                    "row": row_number,
                    "sku": old_sku,
                    "reason": ("Matching checkpoint item not found."),
                }
            )

            continue

        current_status = (
            str(
                checkpoint_item.get(
                    "status",
                    "",
                )
            )
            .strip()
            .lower()
        )

        if current_status != "unmatched":
            skipped_records.append(
                {
                    "row": row_number,
                    "sku": old_sku,
                    "current_status": (current_status),
                    "reason": ("Checkpoint item is no longer unmatched."),
                }
            )

            continue

        previous_status = checkpoint_item.get("status")

        checkpoint_item["status"] = "resolved_same_sku"

        checkpoint_item["resolution_type"] = "recovered_same_sku"

        checkpoint_item["resolved_at"] = resolved_at

        checkpoint_item["resolved_sku"] = old_sku

        checkpoint_item["resolved_product_id"] = (
            str(product_id) if product_id is not None else None
        )

        checkpoint_item["resolution_source"] = (
            "Mobile Sentrix supersession investigation"
        )

        checkpoint_item["resolution_note"] = (
            "Original Mobile Sentrix SKU became "
            "searchable again during supersession "
            "investigation. No SKU replacement was performed."
        )

        resolved_count += 1

        resolved_records.append(
            {
                "row": row_number,
                "sku": old_sku,
                "previous_status": (previous_status),
                "new_status": ("resolved_same_sku"),
                "product_id": (product_id),
            }
        )

    checkpoint["retry_items"] = retry_items

    pending_count = sum(
        1
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
            == "pending"
        )
    )

    unmatched_count = sum(
        1
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
    )

    resolved_same_sku_count = sum(
        1
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
            == "resolved_same_sku"
        )
    )

    resolved_replacement_count = sum(
        1
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
            == "resolved_replacement"
        )
    )

    checkpoint["cycle_complete"] = (
        checkpoint.get("next_start_row") is None and pending_count == 0
    )

    checkpoint["last_resolution_run_at"] = resolved_at

    sync._save_checkpoint(checkpoint)

    resolution_report = {
        "generated_at": (resolved_at),
        "source_report": str(SOURCE_REPORT_PATH),
        "resolved_count": (resolved_count),
        "skipped_count": (len(skipped_records)),
        "resolved_records": (resolved_records),
        "skipped_records": (skipped_records),
        "checkpoint_counts": {
            "pending": (pending_count),
            "unmatched": (unmatched_count),
            "resolved_same_sku": (resolved_same_sku_count),
            "resolved_replacement": (resolved_replacement_count),
        },
        "cycle_complete": (checkpoint.get("cycle_complete")),
    }

    RESOLUTION_REPORT_PATH.write_text(
        json.dumps(
            resolution_report,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)

    print("Supersession same-SKU resolution complete")

    print("=" * 72)

    print(
        "Resolved:",
        resolved_count,
    )

    print(
        "Skipped:",
        len(skipped_records),
    )

    print(
        "Pending:",
        pending_count,
    )

    print(
        "Remaining unmatched:",
        unmatched_count,
    )

    print(
        "Resolved same-SKU:",
        resolved_same_sku_count,
    )

    print(
        "Resolved replacements:",
        resolved_replacement_count,
    )

    print(
        "Cycle complete:",
        checkpoint.get("cycle_complete"),
    )

    print(
        "Resolution report:",
        RESOLUTION_REPORT_PATH,
    )

    print()
    print("No workbook SKU values were changed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
