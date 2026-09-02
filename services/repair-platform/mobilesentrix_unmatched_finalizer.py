from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from integrations.mobilesentrix import (
    MobileSentrixWorkbookSyncService,
)

# ============================================================
# Safety configuration
# ============================================================

APPLY_CHANGES = False


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

REPORT_DIR = BASE_DIR / "Data" / "reports"

SOURCE_REPORT_PATH = REPORT_DIR / "mobilesentrix_supersession_20260901T212521Z.json"

RUN_TIMESTAMP = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

OUTPUT_REPORT_PATH = (
    REPORT_DIR / f"mobilesentrix_unmatched_finalizer_{RUN_TIMESTAMP}.json"
)


# ============================================================
# Helpers
# ============================================================


def normalize_sku(
    value: object,
) -> str:
    return str(value or "").strip()


def normalize_status(
    value: object,
) -> str:
    return str(value or "").strip().lower()


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
    print("Mobile Sentrix Unmatched Finalizer")
    print("=" * 72)

    print(
        "Mode:",
        ("APPLY" if APPLY_CHANGES else "DRY RUN"),
    )

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

    # --------------------------------------------------------
    # Only records still classified remain_unmatched
    # --------------------------------------------------------

    unresolved_report_records: list[dict[str, Any]] = []

    for raw_result in raw_results:
        if not isinstance(
            raw_result,
            dict,
        ):
            continue

        outcome = normalize_status(raw_result.get("outcome"))

        if outcome != "remain_unmatched":
            continue

        unresolved_report_records.append(
            {str(key): value for key, value in raw_result.items()}
        )

    print(
        "Report records marked remain_unmatched:",
        len(unresolved_report_records),
    )

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

    finalized_at = datetime.now(UTC).isoformat()

    eligible_records: list[dict[str, object]] = []

    skipped_records: list[dict[str, object]] = []

    for report_record in unresolved_report_records:
        row_number = safe_int(report_record.get("workbook_row"))

        old_sku = normalize_sku(report_record.get("old_sku"))

        old_product_name = report_record.get("old_product_name")

        if row_number is None:
            skipped_records.append(
                {
                    "row": (report_record.get("workbook_row")),
                    "sku": old_sku,
                    "reason": ("Invalid workbook row."),
                }
            )

            continue

        if not old_sku:
            skipped_records.append(
                {
                    "row": row_number,
                    "sku": old_sku,
                    "reason": ("Old SKU is missing."),
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
                    "reason": ("Matching checkpoint record not found."),
                }
            )

            continue

        current_status = normalize_status(checkpoint_item.get("status"))

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

        eligible_records.append(
            {
                "row": row_number,
                "sku": old_sku,
                "product_name": (old_product_name),
                "checkpoint_item": (checkpoint_item),
            }
        )

    print(
        "Eligible to finalize:",
        len(eligible_records),
    )

    print(
        "Skipped:",
        len(skipped_records),
    )

    # --------------------------------------------------------
    # Apply only when explicitly enabled
    # --------------------------------------------------------

    finalized_records: list[dict[str, object]] = []

    if APPLY_CHANGES:
        for eligible in eligible_records:
            checkpoint_item = eligible["checkpoint_item"]

            if not isinstance(
                checkpoint_item,
                dict,
            ):
                raise RuntimeError(
                    "Validated checkpoint item " "is no longer a dictionary."
                )

            previous_status = checkpoint_item.get("status")

            checkpoint_item["status"] = "supplier_unresolved"

            checkpoint_item["resolution_type"] = "unresolved_after_investigation"

            checkpoint_item["finalized_at"] = finalized_at

            checkpoint_item["last_known_sku"] = eligible["sku"]

            checkpoint_item["last_known_product_name"] = eligible["product_name"]

            checkpoint_item["investigation_report"] = str(SOURCE_REPORT_PATH)

            checkpoint_item["resolution_note"] = (
                "No exact same-SKU recovery, "
                "explicit Mobile Sentrix new_sku, "
                "or verified supplier replacement "
                "was established after investigation."
            )

            finalized_records.append(
                {
                    "row": (eligible["row"]),
                    "sku": (eligible["sku"]),
                    "previous_status": (previous_status),
                    "new_status": ("supplier_unresolved"),
                }
            )

        checkpoint["retry_items"] = retry_items

        checkpoint["last_resolution_run_at"] = finalized_at

        pending_count = sum(
            1
            for item in retry_items
            if (
                isinstance(
                    item,
                    dict,
                )
                and normalize_status(item.get("status")) == "pending"
            )
        )

        checkpoint["cycle_complete"] = (
            checkpoint.get("next_start_row") is None and pending_count == 0
        )

        sync._save_checkpoint(checkpoint)

    # --------------------------------------------------------
    # Final counts
    # --------------------------------------------------------

    status_counts = Counter(
        normalize_status(item.get("status"))
        for item in retry_items
        if isinstance(
            item,
            dict,
        )
    )

    report = {
        "generated_at": (datetime.now(UTC).isoformat()),
        "mode": ("apply" if APPLY_CHANGES else "dry_run"),
        "source_report": str(SOURCE_REPORT_PATH),
        "remain_unmatched_in_report": (len(unresolved_report_records)),
        "eligible_count": (len(eligible_records)),
        "finalized_count": (len(finalized_records)),
        "skipped_count": (len(skipped_records)),
        "eligible_records": [
            {
                "row": (item["row"]),
                "sku": (item["sku"]),
                "product_name": (item["product_name"]),
            }
            for item in eligible_records
        ],
        "finalized_records": (finalized_records),
        "skipped_records": (skipped_records),
        "checkpoint_status_counts": (dict(status_counts)),
        "cycle_complete": (checkpoint.get("cycle_complete")),
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

    print("Unmatched finalizer complete")

    print("=" * 72)

    print(
        "Mode:",
        ("APPLY" if APPLY_CHANGES else "DRY RUN"),
    )

    print(
        "Eligible:",
        len(eligible_records),
    )

    print(
        "Finalized:",
        len(finalized_records),
    )

    print(
        "Skipped:",
        len(skipped_records),
    )

    print(
        "Checkpoint statuses:",
        dict(status_counts),
    )

    print(
        "Cycle complete:",
        checkpoint.get("cycle_complete"),
    )

    print(
        "Report:",
        OUTPUT_REPORT_PATH,
    )

    if not APPLY_CHANGES:
        print()
        print("No checkpoint changes were made.")

    print()
    print("No workbook SKU values were changed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
