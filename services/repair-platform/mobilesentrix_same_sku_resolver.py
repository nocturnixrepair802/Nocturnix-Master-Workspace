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

SOURCE_REPORT_PATH = REPORT_DIR / "mobilesentrix_unmatched_20260901T150820Z.json"

RUN_TIMESTAMP = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

RESOLUTION_REPORT_PATH = (
    REPORT_DIR / f"mobilesentrix_same_sku_resolution_{RUN_TIMESTAMP}.json"
)

TARGET_OUTCOME = "recovered_same_sku"


# ============================================================
# Helpers
# ============================================================


def normalize_sku(
    value: object,
) -> str:
    return str(value or "").strip()


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

    print("Mobile Sentrix Same-SKU Resolver")

    print("=" * 72)

    print(
        "Source investigation report:",
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

        selected_candidate = raw_result.get("selected_candidate")

        if not isinstance(
            selected_candidate,
            dict,
        ):
            continue

        candidate_sku = normalize_sku(selected_candidate.get("sku"))

        if not old_sku or not candidate_sku or old_sku != candidate_sku:
            continue

        recovered_results.append(raw_result)

    print(
        "Recovered same-SKU records found:",
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
        row_raw = recovered.get("workbook_row")

        old_sku = normalize_sku(recovered.get("old_sku"))

        selected_candidate = recovered.get("selected_candidate")

        if not isinstance(
            selected_candidate,
            dict,
        ):
            continue

        candidate_sku = normalize_sku(selected_candidate.get("sku"))

        candidate_product_id = selected_candidate.get("product_id")

        candidate_score = selected_candidate.get("score")

        try:
            row_number = int(str(row_raw))

        except (
            ValueError,
            TypeError,
        ):
            skipped_records.append(
                {
                    "row": row_raw,
                    "sku": old_sku,
                    "reason": ("Invalid workbook row."),
                }
            )

            continue

        matching_checkpoint_item: dict[str, object] | None = None

        for item in retry_items:
            if not isinstance(
                item,
                dict,
            ):
                continue

            item_row = item.get("row")

            item_sku = normalize_sku(item.get("sku"))

            try:
                item_row_number = int(str(item_row))

            except (
                ValueError,
                TypeError,
            ):
                continue

            if item_row_number == row_number and item_sku == old_sku:
                matching_checkpoint_item = item
                break

        if matching_checkpoint_item is None:
            skipped_records.append(
                {
                    "row": row_number,
                    "sku": old_sku,
                    "reason": ("Matching checkpoint record not found."),
                }
            )

            continue

        current_status = (
            str(
                matching_checkpoint_item.get(
                    "status",
                    "",
                )
            )
            .strip()
            .lower()
        )

        if current_status not in {
            "unmatched",
            "recovered_same_sku",
        }:
            skipped_records.append(
                {
                    "row": row_number,
                    "sku": old_sku,
                    "reason": ("Checkpoint item is not currently unmatched."),
                    "current_status": (current_status),
                }
            )

            continue

        if old_sku != candidate_sku:
            skipped_records.append(
                {
                    "row": row_number,
                    "sku": old_sku,
                    "candidate_sku": (candidate_sku),
                    "reason": ("Candidate SKU does not equal old SKU."),
                }
            )

            continue

        previous_status = matching_checkpoint_item.get("status")

        matching_checkpoint_item["status"] = "resolved_same_sku"

        matching_checkpoint_item["resolution_type"] = "recovered_same_sku"

        matching_checkpoint_item["resolved_at"] = resolved_at

        matching_checkpoint_item["resolved_sku"] = old_sku

        matching_checkpoint_item["resolved_product_id"] = (
            str(candidate_product_id) if candidate_product_id is not None else None
        )

        matching_checkpoint_item["resolution_score"] = candidate_score

        matching_checkpoint_item["resolution_note"] = (
            "Original Mobile Sentrix SKU became "
            "searchable again. No SKU replacement "
            "was performed."
        )

        resolved_count += 1

        resolved_records.append(
            {
                "row": row_number,
                "sku": old_sku,
                "previous_status": (previous_status),
                "new_status": ("resolved_same_sku"),
                "product_id": (candidate_product_id),
                "score": (candidate_score),
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

    checkpoint["cycle_complete"] = (
        checkpoint.get("next_start_row") is None and pending_count == 0
    )

    checkpoint["last_resolution_run_at"] = resolved_at

    # --------------------------------------------------------
    # Save checkpoint only after all validation is complete.
    # --------------------------------------------------------

    sync._save_checkpoint(checkpoint)

    resolution_report = {
        "generated_at": resolved_at,
        "source_report": str(SOURCE_REPORT_PATH),
        "resolved_count": (resolved_count),
        "skipped_count": (len(skipped_records)),
        "resolved_records": (resolved_records),
        "skipped_records": (skipped_records),
        "checkpoint_counts": {
            "pending": (pending_count),
            "unmatched": (unmatched_count),
            "resolved_same_sku": (resolved_same_sku_count),
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

    print("Same-SKU resolution complete")

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
