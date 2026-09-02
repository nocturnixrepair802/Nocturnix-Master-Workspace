from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO
from urllib.error import URLError
from urllib.request import Request, urlopen

from integrations.mobilesentrix import (
    MobileSentrixWorkbookSyncService,
)

# ============================================================
# Runner configuration
# ============================================================

BATCH_SIZE = 200

REQUEST_DELAY_SECONDS = 0.10

PAUSE_BETWEEN_BATCHES_SECONDS = 2.0

RETRY_EVERY_BATCHES = 10

RETRY_MAX_ITEMS = 25

MAX_BATCH_API_ERRORS = 10

MAX_BATCHES_PER_RUN = 50


# ============================================================
# Dedicated IP / VPN safety configuration
# ============================================================

EXPECTED_PUBLIC_IP = "149.174.198.187"

PUBLIC_IP_CHECK_URL = "https://api.ipify.org"

PUBLIC_IP_TIMEOUT_SECONDS = 15

PUBLIC_IP_CHECK_ATTEMPTS = 3

PUBLIC_IP_RETRY_DELAY_SECONDS = 5.0


# ============================================================
# Logging
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "Data" / "logs"

RUN_TIMESTAMP = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

LOG_PATH = LOG_DIR / f"mobilesentrix_sync_{RUN_TIMESTAMP}.log"

LATEST_LOG_PATH = LOG_DIR / "mobilesentrix_sync_latest.log"

STATE_PATH = LOG_DIR / "mobilesentrix_sync_runner_state.json"


# ============================================================
# Retry/history status names
# ============================================================

STATUS_PENDING = "pending"

STATUS_UNMATCHED = "unmatched"

STATUS_EXHAUSTED = "exhausted"

STATUS_RESOLVED_SAME_SKU = "resolved_same_sku"

STATUS_RESOLVED_REPLACEMENT = "resolved_replacement"

STATUS_SUPPLIER_UNRESOLVED = "supplier_unresolved"


# ============================================================
# Tee output
# ============================================================


class Tee:
    """
    Write output to multiple streams.

    Terminal output continues normally while the same
    information is persisted to the run log and latest log.
    """

    def __init__(
        self,
        *streams: TextIO,
    ) -> None:
        self.streams = streams

    def write(
        self,
        data: str,
    ) -> int:
        for stream in self.streams:
            stream.write(data)

            stream.flush()

        return len(data)

    def flush(
        self,
    ) -> None:
        for stream in self.streams:
            stream.flush()


# ============================================================
# General helpers
# ============================================================


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def get_int(
    value: object,
    default: int = 0,
) -> int:
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

    if isinstance(
        value,
        float,
    ):
        return int(value)

    if isinstance(
        value,
        str,
    ):
        try:
            return int(value)

        except ValueError:
            return default

    return default


def normalize_status(
    value: object,
) -> str:
    return str(value or "").strip().lower()


# ============================================================
# Retry/history helpers
# ============================================================


def get_retry_count(
    checkpoint: dict[str, object],
) -> int:
    retry_items = checkpoint.get(
        "retry_items",
        [],
    )

    if not isinstance(
        retry_items,
        list,
    ):
        return 0

    return len(retry_items)


def get_retry_status_counts(
    checkpoint: dict[str, object],
) -> tuple[
    int,
    int,
    int,
    int,
    int,
    int,
    int,
]:
    """
    Return retry/history counts in this order:

        pending
        unmatched
        exhausted
        resolved_same_sku
        resolved_replacement
        supplier_unresolved
        other
    """

    retry_items = checkpoint.get(
        "retry_items",
        [],
    )

    if not isinstance(
        retry_items,
        list,
    ):
        return (
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        )

    pending = 0

    unmatched = 0

    exhausted = 0

    resolved_same_sku = 0

    resolved_replacement = 0

    supplier_unresolved = 0

    other = 0

    for item in retry_items:
        if not isinstance(
            item,
            dict,
        ):
            other += 1
            continue

        status = normalize_status(item.get("status"))

        if status == STATUS_PENDING:
            pending += 1

        elif status == STATUS_UNMATCHED:
            unmatched += 1

        elif status == STATUS_EXHAUSTED:
            exhausted += 1

        elif status == STATUS_RESOLVED_SAME_SKU:
            resolved_same_sku += 1

        elif status == STATUS_RESOLVED_REPLACEMENT:
            resolved_replacement += 1

        elif status == STATUS_SUPPLIER_UNRESOLVED:
            supplier_unresolved += 1

        else:
            other += 1

    return (
        pending,
        unmatched,
        exhausted,
        resolved_same_sku,
        resolved_replacement,
        supplier_unresolved,
        other,
    )


def get_actionable_retry_count(
    checkpoint: dict[str, object],
) -> int:
    (
        pending,
        unmatched,
        exhausted,
        _resolved_same_sku,
        _resolved_replacement,
        _supplier_unresolved,
        _other,
    ) = get_retry_status_counts(checkpoint)

    return pending + unmatched + exhausted


def get_pending_retry_count(
    checkpoint: dict[str, object],
) -> int:
    (
        pending,
        _unmatched,
        _exhausted,
        _resolved_same_sku,
        _resolved_replacement,
        _supplier_unresolved,
        _other,
    ) = get_retry_status_counts(checkpoint)

    return pending


# ============================================================
# Dedicated-IP helpers
# ============================================================


def get_public_ip() -> str:
    request = Request(
        PUBLIC_IP_CHECK_URL,
        headers={
            "Accept": ("text/plain"),
            "User-Agent": ("Nocturnix-MobileSentrix-Sync/1.0"),
        },
        method="GET",
    )

    with urlopen(
        request,
        timeout=(PUBLIC_IP_TIMEOUT_SECONDS),
    ) as response:
        value = response.read().decode(
            "utf-8",
            errors="replace",
        )

    return value.strip()


def verify_public_ip(
    *,
    batch_number: int | None = None,
) -> tuple[
    bool,
    str | None,
]:
    print()
    print("VPN / Dedicated IP Check")
    print("------------------------")

    if batch_number is not None:
        print(
            "Batch:",
            batch_number,
        )

    public_ip: str | None = None

    for attempt in range(
        1,
        PUBLIC_IP_CHECK_ATTEMPTS + 1,
    ):
        try:
            public_ip = get_public_ip()

        except (
            URLError,
            TimeoutError,
            OSError,
        ) as exc:
            print(f"Attempt {attempt}: " "unable to determine " "public IP.")

            print(
                "Reason:",
                str(exc),
            )

            if attempt < PUBLIC_IP_CHECK_ATTEMPTS:
                print(
                    "Waiting",
                    PUBLIC_IP_RETRY_DELAY_SECONDS,
                    "seconds before retry...",
                )

                time.sleep(PUBLIC_IP_RETRY_DELAY_SECONDS)

                continue

            return (
                False,
                None,
            )

        print(
            f"Attempt {attempt}:",
            public_ip,
        )

        if public_ip == EXPECTED_PUBLIC_IP:
            print("Dedicated IP validation: PASS")

            return (
                True,
                public_ip,
            )

        print("Dedicated IP validation: FAIL")

        print(
            "Expected:",
            EXPECTED_PUBLIC_IP,
        )

        print(
            "Received:",
            public_ip,
        )

        if attempt < PUBLIC_IP_CHECK_ATTEMPTS:
            print(
                "Waiting",
                PUBLIC_IP_RETRY_DELAY_SECONDS,
                "seconds before retry...",
            )

            time.sleep(PUBLIC_IP_RETRY_DELAY_SECONDS)

    return (
        False,
        public_ip,
    )


# ============================================================
# Runner-state persistence
# ============================================================


def write_state_snapshot(
    *,
    sync: MobileSentrixWorkbookSyncService,
    event: str,
    batch_number: int | None = None,
    extra: dict[str, object] | None = None,
) -> None:
    try:
        checkpoint = sync.get_sync_checkpoint()

        snapshot: dict[
            str,
            object,
        ] = {
            "timestamp": (utc_now()),
            "event": (event),
            "batch_number": (batch_number),
            "checkpoint": (checkpoint),
        }

        if extra:
            snapshot["extra"] = extra

        temporary_path = STATE_PATH.with_suffix(".json.tmp")

        temporary_path.write_text(
            json.dumps(
                snapshot,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(STATE_PATH)

    except Exception:
        print()
        print("WARNING: Unable to write " "runner state snapshot.")

        traceback.print_exc()


# ============================================================
# Terminal reporting
# ============================================================


def print_header() -> None:
    print()
    print("=" * 72)

    print("Nocturnix Mobile Sentrix " "Catalog Sync Runner")

    print("=" * 72)

    print(
        "Started:",
        utc_now(),
    )

    print(
        "Batch size:",
        BATCH_SIZE,
    )

    print(
        "Request delay:",
        REQUEST_DELAY_SECONDS,
        "seconds",
    )

    print(
        "Pause between batches:",
        PAUSE_BETWEEN_BATCHES_SECONDS,
        "seconds",
    )

    print(
        "Retry every:",
        RETRY_EVERY_BATCHES,
        "batches",
    )

    print(
        "Maximum retry items per pass:",
        RETRY_MAX_ITEMS,
    )

    print(
        "Maximum batch API errors:",
        MAX_BATCH_API_ERRORS,
    )

    print(
        "Retry queue safety:",
        "informational only",
    )

    print(
        "Maximum batches this run:",
        MAX_BATCHES_PER_RUN,
    )

    print(
        "Expected public IP:",
        EXPECTED_PUBLIC_IP,
    )

    print(
        "Run log:",
        LOG_PATH,
    )

    print(
        "Latest log:",
        LATEST_LOG_PATH,
    )

    print(
        "State file:",
        STATE_PATH,
    )

    print()


def print_checkpoint(
    checkpoint: dict[str, object],
) -> None:
    retry_count = get_retry_count(checkpoint)

    (
        pending_count,
        unmatched_count,
        exhausted_count,
        resolved_same_sku_count,
        resolved_replacement_count,
        supplier_unresolved_count,
        other_count,
    ) = get_retry_status_counts(checkpoint)

    print("Current checkpoint")

    print("------------------")

    print(
        "Next start row:",
        checkpoint.get("next_start_row"),
    )

    print(
        "Products processed this cycle:",
        checkpoint.get("products_processed_this_cycle"),
    )

    print(
        "Retry/history records:",
        retry_count,
    )

    print()

    print(
        "Pending retries:",
        pending_count,
    )

    print(
        "Unmatched retries:",
        unmatched_count,
    )

    print(
        "Exhausted retries:",
        exhausted_count,
    )

    print()

    print(
        "Resolved same SKU:",
        resolved_same_sku_count,
    )

    print(
        "Resolved replacement:",
        resolved_replacement_count,
    )

    print(
        "Supplier unresolved:",
        supplier_unresolved_count,
    )

    print(
        "Other states:",
        other_count,
    )

    print()

    print(
        "Cycle complete:",
        checkpoint.get("cycle_complete"),
    )

    print()


def print_sync_completion_summary(
    checkpoint: dict[str, object],
) -> None:
    (
        pending_count,
        unmatched_count,
        exhausted_count,
        resolved_same_sku_count,
        resolved_replacement_count,
        supplier_unresolved_count,
        other_count,
    ) = get_retry_status_counts(checkpoint)

    actionable_count = pending_count + unmatched_count + exhausted_count

    historical_count = (
        resolved_same_sku_count + resolved_replacement_count + supplier_unresolved_count
    )

    print("Synchronization cycle is already complete.")

    if actionable_count == 0:
        print("No actionable retry items remain.")

    else:
        print(
            "Actionable retry/history " "items remain:",
            actionable_count,
        )

    if historical_count > 0:
        print(
            "Historical resolution records " "remain preserved:",
            historical_count,
        )

    if other_count > 0:
        print(
            "Unrecognized retry/history states:",
            other_count,
        )


def print_batch_result(
    *,
    batch_number: int,
    result: dict[str, object],
) -> None:
    print()
    print("-" * 72)

    print(f"Batch {batch_number}")

    print("-" * 72)

    fields = [
        (
            "Products processed",
            "products_processed",
        ),
        (
            "Exact matches",
            "exact_matches",
        ),
        (
            "Rows updated",
            "rows_updated",
        ),
        (
            "Unchanged rows",
            "unchanged_rows",
        ),
        (
            "Not found",
            "not_found",
        ),
        (
            "Ambiguous matches",
            "ambiguous_matches",
        ),
        (
            "API errors",
            "api_errors",
        ),
        (
            "Next start row",
            "next_start_row",
        ),
        (
            "Retry count",
            "retry_count",
        ),
        (
            "Processed this cycle",
            "products_processed_this_cycle",
        ),
        (
            "Cycle complete",
            "cycle_complete",
        ),
    ]

    for (
        label,
        key,
    ) in fields:
        print(
            f"{label}:",
            result.get(key),
        )

    errors = result.get("errors")

    if (
        isinstance(
            errors,
            list,
        )
        and errors
    ):
        print()
        print("Items queued for retry:")

        for error in errors:
            print(error)


# ============================================================
# Retry processing
# ============================================================


def run_retry_pass(
    sync: MobileSentrixWorkbookSyncService,
) -> dict[str, object]:
    checkpoint = sync.get_sync_checkpoint()

    pending_before = get_pending_retry_count(checkpoint)

    if pending_before <= 0:
        print()
        print("Retry pass skipped: " "no pending retry items remain.")

        return {
            "retry_items_processed": 0,
            "recovered": 0,
            "still_pending": 0,
            "unmatched": 0,
            "exhausted": 0,
            "api_errors": 0,
            "retry_count": (get_retry_count(checkpoint)),
        }

    print()
    print("Running retry pass...")

    try:
        result = sync.retry_failed_items(
            max_items=(RETRY_MAX_ITEMS),
            request_delay_seconds=(REQUEST_DELAY_SECONDS),
        )

    except Exception as exc:
        print()
        print("RETRY PASS FAILED")

        print(
            "Exception type:",
            type(exc).__name__,
        )

        print(
            "Exception:",
            str(exc),
        )

        print()

        traceback.print_exc()

        write_state_snapshot(
            sync=sync,
            event=("retry_pass_exception"),
            extra={
                "exception_type": (type(exc).__name__),
                "exception": (str(exc)),
            },
        )

        raise

    print(
        "Retry items processed:",
        result.get(
            "retry_items_processed",
            0,
        ),
    )

    print(
        "Recovered:",
        result.get(
            "recovered",
            0,
        ),
    )

    print(
        "Still pending:",
        result.get(
            "still_pending",
            0,
        ),
    )

    print(
        "Unmatched:",
        result.get(
            "unmatched",
            0,
        ),
    )

    print(
        "Exhausted:",
        result.get(
            "exhausted",
            0,
        ),
    )

    print(
        "Retry API errors:",
        result.get(
            "api_errors",
            0,
        ),
    )

    print(
        "Retry count remaining:",
        result.get(
            "retry_count",
            0,
        ),
    )

    return result


# ============================================================
# Main runner
# ============================================================


def run() -> int:
    print_header()

    print("Initializing synchronization service...")

    sync = MobileSentrixWorkbookSyncService()

    print("Synchronization service initialized.")

    print()

    checkpoint = sync.get_sync_checkpoint()

    print_checkpoint(checkpoint)

    # ========================================================
    # Already-complete cycle
    #
    # Do this before making any external IP request.
    # Final historical statuses are not retry work.
    # ========================================================

    (
        pending_count,
        unmatched_count,
        exhausted_count,
        _resolved_same_sku_count,
        _resolved_replacement_count,
        _supplier_unresolved_count,
        _other_count,
    ) = get_retry_status_counts(checkpoint)

    next_start_row = checkpoint.get("next_start_row")

    cycle_complete = bool(
        checkpoint.get(
            "cycle_complete",
            False,
        )
    )

    if (
        cycle_complete
        and next_start_row is None
        and pending_count == 0
        and unmatched_count == 0
        and exhausted_count == 0
    ):
        print_sync_completion_summary(checkpoint)

        write_state_snapshot(
            sync=sync,
            event=("already_complete"),
            extra={
                "pending_retries": (pending_count),
                "unmatched_retries": (unmatched_count),
                "exhausted_retries": (exhausted_count),
            },
        )

        return 0

    # ========================================================
    # Initial Dedicated IP verification
    #
    # Required only if API work may actually be performed.
    # ========================================================

    ip_ok, public_ip = verify_public_ip()

    if not ip_ok:
        print()
        print("STOPPING:")

        print("Dedicated public IP " "validation failed.")

        print(
            "Expected:",
            EXPECTED_PUBLIC_IP,
        )

        print(
            "Received:",
            public_ip,
        )

        print("Reconnect NordVPN to the " "Dedicated IP before restarting.")

        write_state_snapshot(
            sync=sync,
            event=("initial_public_ip_" "validation_failed"),
            extra={
                "expected_public_ip": (EXPECTED_PUBLIC_IP),
                "received_public_ip": (public_ip),
            },
        )

        return 2

    write_state_snapshot(
        sync=sync,
        event=("runner_started"),
        extra={
            "public_ip": (public_ip),
        },
    )

    batches_completed = 0

    while batches_completed < MAX_BATCHES_PER_RUN:
        checkpoint = sync.get_sync_checkpoint()

        next_start_row = checkpoint.get("next_start_row")

        (
            pending_count,
            unmatched_count,
            exhausted_count,
            resolved_same_sku_count,
            resolved_replacement_count,
            supplier_unresolved_count,
            other_count,
        ) = get_retry_status_counts(checkpoint)

        # ==================================================
        # Primary scan finished
        # ==================================================

        if next_start_row is None:
            if pending_count > 0:
                print()
                print("Primary scan is complete.")

                print(f"{pending_count} pending " "retry item(s) remain.")

                # Verify dedicated IP again immediately
                # before making retry API requests.
                ip_ok, public_ip = verify_public_ip()

                if not ip_ok:
                    print()
                    print("STOPPING:")

                    print(
                        "Dedicated public IP "
                        "could not be verified "
                        "before retry processing."
                    )

                    write_state_snapshot(
                        sync=sync,
                        event=("retry_public_ip_" "safety_stop"),
                    )

                    return 2

                retry_result = run_retry_pass(sync)

                checkpoint = sync.get_sync_checkpoint()

                (
                    pending_count,
                    unmatched_count,
                    exhausted_count,
                    resolved_same_sku_count,
                    resolved_replacement_count,
                    supplier_unresolved_count,
                    other_count,
                ) = get_retry_status_counts(checkpoint)

                if pending_count == 0:
                    print()
                    print("No pending retries remain.")

                    if unmatched_count > 0 or exhausted_count > 0:
                        print("Manual-review retry " "states remain recorded.")

                    else:
                        print("Primary synchronization " "work is complete.")

                    write_state_snapshot(
                        sync=sync,
                        event=("primary_scan_" "retry_processing_complete"),
                        extra={
                            "pending_retries": (pending_count),
                            "unmatched_retries": (unmatched_count),
                            "exhausted_retries": (exhausted_count),
                            "resolved_same_sku": (resolved_same_sku_count),
                            "resolved_replacement": (resolved_replacement_count),
                            "supplier_unresolved": (supplier_unresolved_count),
                            "other_states": (other_count),
                            "retry_result": (retry_result),
                        },
                    )

                    break

                print()
                print("Pending retry items remain.")

                print(
                    "Stopping this runner so " "they are not retried " "continuously."
                )

                write_state_snapshot(
                    sync=sync,
                    event=("primary_complete_" "pending_retries"),
                    extra={
                        "pending_retries": (pending_count),
                    },
                )

                break

            # There are no pending retries. Unmatched/exhausted
            # records require review, not continuous retries.
            if unmatched_count > 0 or exhausted_count > 0:
                print()
                print("Primary scan is complete.")

                if unmatched_count > 0:
                    print(
                        "Unmatched retry items " "remain for investigation:",
                        unmatched_count,
                    )

                if exhausted_count > 0:
                    print(
                        "Exhausted retry items " "remain for manual review:",
                        exhausted_count,
                    )

                print("No automatic retry work " "will be performed.")

                write_state_snapshot(
                    sync=sync,
                    event=("primary_complete_" "manual_review_required"),
                    extra={
                        "unmatched_retries": (unmatched_count),
                        "exhausted_retries": (exhausted_count),
                    },
                )

                break

            print()
            print("Primary scan is complete.")

            print("No actionable retry items remain.")

            historical_count = (
                resolved_same_sku_count
                + resolved_replacement_count
                + supplier_unresolved_count
            )

            if historical_count > 0:
                print(
                    "Historical resolution " "records remain preserved:",
                    historical_count,
                )

            if other_count > 0:
                print(
                    "Unrecognized retry/history " "states remain:",
                    other_count,
                )

            write_state_snapshot(
                sync=sync,
                event=("primary_scan_complete"),
                extra={
                    "pending_retries": (pending_count),
                    "unmatched_retries": (unmatched_count),
                    "exhausted_retries": (exhausted_count),
                    "resolved_same_sku": (resolved_same_sku_count),
                    "resolved_replacement": (resolved_replacement_count),
                    "supplier_unresolved": (supplier_unresolved_count),
                    "other_states": (other_count),
                },
            )

            break

        batch_number = batches_completed + 1

        # ==================================================
        # Verify VPN / Dedicated IP BEFORE every batch
        # ==================================================

        ip_ok, public_ip = verify_public_ip(
            batch_number=(batch_number),
        )

        if not ip_ok:
            print()
            print("STOPPING:")

            print("Dedicated public IP changed " "or could not be verified.")

            print(
                "Expected:",
                EXPECTED_PUBLIC_IP,
            )

            print(
                "Received:",
                public_ip,
            )

            print("No Mobile Sentrix batch " "was started.")

            write_state_snapshot(
                sync=sync,
                event=("public_ip_safety_stop"),
                batch_number=(batch_number),
                extra={
                    "expected_public_ip": (EXPECTED_PUBLIC_IP),
                    "received_public_ip": (public_ip),
                    "start_row": (next_start_row),
                },
            )

            return 2

        # ==================================================
        # Run normal batch
        # ==================================================

        print()
        print(
            f"Starting batch "
            f"{batch_number} "
            f"from workbook row "
            f"{next_start_row}..."
        )

        print(
            "Public IP:",
            public_ip,
        )

        write_state_snapshot(
            sync=sync,
            event=("batch_starting"),
            batch_number=(batch_number),
            extra={
                "start_row": (next_start_row),
                "public_ip": (public_ip),
            },
        )

        try:
            result = sync.sync_next_batch(
                batch_size=(BATCH_SIZE),
                request_delay_seconds=(REQUEST_DELAY_SECONDS),
            )

        except KeyboardInterrupt:
            print()
            print()
            print("RUN INTERRUPTED BY USER")

            print("KeyboardInterrupt received.")

            write_state_snapshot(
                sync=sync,
                event=("keyboard_interrupt"),
                batch_number=(batch_number),
            )

            return 130

        except Exception as exc:
            print()
            print()
            print("BATCH FAILED WITH EXCEPTION")

            print(
                "Batch:",
                batch_number,
            )

            print(
                "Start row:",
                next_start_row,
            )

            print(
                "Public IP:",
                public_ip,
            )

            print(
                "Exception type:",
                type(exc).__name__,
            )

            print(
                "Exception:",
                str(exc),
            )

            print()

            traceback.print_exc()

            write_state_snapshot(
                sync=sync,
                event=("batch_exception"),
                batch_number=(batch_number),
                extra={
                    "start_row": (next_start_row),
                    "public_ip": (public_ip),
                    "exception_type": (type(exc).__name__),
                    "exception": (str(exc)),
                },
            )

            return 1

        batches_completed += 1

        print_batch_result(
            batch_number=(batch_number),
            result=result,
        )

        write_state_snapshot(
            sync=sync,
            event=("batch_completed"),
            batch_number=(batch_number),
            extra={
                "public_ip": (public_ip),
                "products_processed": (result.get("products_processed")),
                "exact_matches": (result.get("exact_matches")),
                "api_errors": (result.get("api_errors")),
                "retry_count": (result.get("retry_count")),
                "next_start_row": (result.get("next_start_row")),
            },
        )

        api_errors = get_int(result.get("api_errors"))

        products_processed = get_int(result.get("products_processed"))

        # ==================================================
        # Safety stops
        # ==================================================

        if api_errors >= MAX_BATCH_API_ERRORS:
            print()
            print("STOPPING:")

            print("The batch reached the API " "error safety threshold.")

            write_state_snapshot(
                sync=sync,
                event=("api_error_safety_stop"),
                batch_number=(batch_number),
                extra={
                    "api_errors": (api_errors),
                },
            )

            break

        if products_processed == 0:
            print()
            print("STOPPING:")

            print("The batch processed " "zero products.")

            write_state_snapshot(
                sync=sync,
                event=("zero_products_" "safety_stop"),
                batch_number=(batch_number),
            )

            break

        # ==================================================
        # Retry queue observation
        #
        # Historical and finalized records do not trigger
        # a queue-size safety stop.
        # ==================================================

        checkpoint = sync.get_sync_checkpoint()

        current_pending = get_pending_retry_count(checkpoint)

        if current_pending > 0:
            print()
            print(
                "Pending retry items:",
                current_pending,
            )

        # ==================================================
        # Periodic retry processing
        # ==================================================

        if batches_completed % RETRY_EVERY_BATCHES == 0:
            checkpoint = sync.get_sync_checkpoint()

            pending_before_retry = get_pending_retry_count(checkpoint)

            if pending_before_retry > 0:
                ip_ok, public_ip = verify_public_ip()

                if not ip_ok:
                    print()
                    print("STOPPING:")

                    print(
                        "Dedicated IP could "
                        "not be verified before "
                        "retry processing."
                    )

                    write_state_snapshot(
                        sync=sync,
                        event=("periodic_retry_" "public_ip_stop"),
                        batch_number=(batch_number),
                    )

                    return 2

                retry_result = run_retry_pass(sync)

                write_state_snapshot(
                    sync=sync,
                    event=("retry_pass_completed"),
                    batch_number=(batch_number),
                    extra={
                        "retry_items_processed": (
                            retry_result.get("retry_items_processed")
                        ),
                        "recovered": (retry_result.get("recovered")),
                        "still_pending": (retry_result.get("still_pending")),
                        "unmatched": (retry_result.get("unmatched")),
                        "exhausted": (retry_result.get("exhausted")),
                        "retry_count": (retry_result.get("retry_count")),
                    },
                )

        # ==================================================
        # Check whether primary scan finished
        # ==================================================

        checkpoint = sync.get_sync_checkpoint()

        next_start_row = checkpoint.get("next_start_row")

        (
            pending_count,
            unmatched_count,
            exhausted_count,
            resolved_same_sku_count,
            resolved_replacement_count,
            supplier_unresolved_count,
            other_count,
        ) = get_retry_status_counts(checkpoint)

        if next_start_row is None and pending_count == 0:
            print()
            print("Primary scan is complete.")

            if unmatched_count > 0:
                print(
                    "Unmatched retry items " "remain for investigation:",
                    unmatched_count,
                )

            if exhausted_count > 0:
                print(
                    "Exhausted retry items " "remain for manual review:",
                    exhausted_count,
                )

            if unmatched_count == 0 and exhausted_count == 0:
                print("No actionable retry " "items remain.")

            historical_count = (
                resolved_same_sku_count
                + resolved_replacement_count
                + supplier_unresolved_count
            )

            if historical_count > 0:
                print(
                    "Historical resolution " "records remain preserved:",
                    historical_count,
                )

            if other_count > 0:
                print(
                    "Unrecognized retry/history " "states:",
                    other_count,
                )

            write_state_snapshot(
                sync=sync,
                event=("primary_scan_complete"),
                batch_number=(batch_number),
                extra={
                    "pending_retries": (pending_count),
                    "unmatched_retries": (unmatched_count),
                    "exhausted_retries": (exhausted_count),
                    "resolved_same_sku": (resolved_same_sku_count),
                    "resolved_replacement": (resolved_replacement_count),
                    "supplier_unresolved": (supplier_unresolved_count),
                    "other_states": (other_count),
                },
            )

            break

        # ==================================================
        # Pause before next batch
        # ==================================================

        if batches_completed < MAX_BATCHES_PER_RUN:
            print()
            print(
                "Waiting",
                PAUSE_BETWEEN_BATCHES_SECONDS,
                "seconds before next batch...",
            )

            time.sleep(PAUSE_BETWEEN_BATCHES_SECONDS)

    # ========================================================
    # Normal runner stop
    # ========================================================

    print()
    print("=" * 72)

    print("Mobile Sentrix runner stopped")

    print("=" * 72)

    print(
        "Stopped:",
        utc_now(),
    )

    print(
        "Batches completed this run:",
        batches_completed,
    )

    print()

    final_checkpoint = sync.get_sync_checkpoint()

    print_checkpoint(final_checkpoint)

    write_state_snapshot(
        sync=sync,
        event=("runner_stopped_normally"),
        extra={
            "batches_completed": (batches_completed),
        },
    )

    return 0


# ============================================================
# Process entrypoint / logging
# ============================================================


def main() -> int:
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_stdout = sys.stdout

    original_stderr = sys.stderr

    with LOG_PATH.open(
        "a",
        encoding="utf-8",
        buffering=1,
    ) as run_log:
        with LATEST_LOG_PATH.open(
            "a",
            encoding="utf-8",
            buffering=1,
        ) as latest_log:
            tee_stdout = Tee(
                original_stdout,
                run_log,
                latest_log,
            )

            tee_stderr = Tee(
                original_stderr,
                run_log,
                latest_log,
            )

            sys.stdout = tee_stdout

            sys.stderr = tee_stderr

            try:
                return run()

            except KeyboardInterrupt:
                print()
                print()
                print("RUNNER INTERRUPTED")

                print("KeyboardInterrupt received " "outside a batch.")

                return 130

            except BaseException as exc:
                print()
                print()

                print("=" * 72)

                print("UNHANDLED RUNNER FAILURE")

                print("=" * 72)

                print(
                    "Timestamp:",
                    utc_now(),
                )

                print(
                    "Exception type:",
                    type(exc).__name__,
                )

                print(
                    "Exception:",
                    str(exc),
                )

                print()

                traceback.print_exc()

                return 1

            finally:
                sys.stdout.flush()
                sys.stderr.flush()

                sys.stdout = original_stdout

                sys.stderr = original_stderr


if __name__ == "__main__":
    raise SystemExit(main())
