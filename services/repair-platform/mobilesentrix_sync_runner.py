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


class Tee:
    """
    Write output to multiple streams.

    This keeps normal terminal output while also writing
    the same output to persistent log files.
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

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def get_int(
    value: object,
    default: int = 0,
) -> int:
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default

    return default


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
) -> tuple[int, int, int, int]:
    """
    Return retry-state counts in this order:

    pending,
    unmatched,
    exhausted,
    other.
    """

    retry_items = checkpoint.get(
        "retry_items",
        [],
    )

    if not isinstance(
        retry_items,
        list,
    ):
        return 0, 0, 0, 0

    pending = 0
    unmatched = 0
    exhausted = 0
    other = 0

    for item in retry_items:
        if not isinstance(
            item,
            dict,
        ):
            other += 1
            continue

        status = (
            str(
                item.get(
                    "status",
                    "",
                )
            )
            .strip()
            .lower()
        )

        if status == "pending":
            pending += 1

        elif status == "unmatched":
            unmatched += 1

        elif status == "exhausted":
            exhausted += 1

        else:
            other += 1

    return (
        pending,
        unmatched,
        exhausted,
        other,
    )


def get_public_ip() -> str:
    request = Request(
        PUBLIC_IP_CHECK_URL,
        headers={
            "Accept": "text/plain",
            "User-Agent": ("Nocturnix-MobileSentrix-Sync/1.0"),
        },
        method="GET",
    )

    with urlopen(
        request,
        timeout=PUBLIC_IP_TIMEOUT_SECONDS,
    ) as response:
        value = response.read().decode(
            "utf-8",
            errors="replace",
        )

    return value.strip()


def verify_public_ip(
    *,
    batch_number: int | None = None,
) -> tuple[bool, str | None]:
    print()
    print("VPN / Dedicated IP Check")
    print("------------------------")

    if batch_number is not None:
        print(
            "Preparing batch:",
            batch_number,
        )

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
            print(f"Attempt {attempt}: " "unable to determine public IP.")

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


def write_state_snapshot(
    *,
    sync: MobileSentrixWorkbookSyncService,
    event: str,
    batch_number: int | None = None,
    extra: dict[str, object] | None = None,
) -> None:
    try:
        checkpoint = sync.get_sync_checkpoint()

        (
            pending_count,
            unmatched_count,
            exhausted_count,
            other_count,
        ) = get_retry_status_counts(checkpoint)

        snapshot: dict[str, object] = {
            "timestamp": utc_now(),
            "event": event,
            "batch_number": batch_number,
            "checkpoint": checkpoint,
            "retry_status": {
                "pending": pending_count,
                "unmatched": unmatched_count,
                "exhausted": exhausted_count,
                "other": other_count,
            },
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
    sync: MobileSentrixWorkbookSyncService,
) -> None:
    checkpoint = sync.get_sync_checkpoint()

    retry_count = get_retry_count(checkpoint)

    (
        pending_count,
        unmatched_count,
        exhausted_count,
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
        "Retry count:",
        retry_count,
    )

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

    if other_count:
        print(
            "Other retry states:",
            other_count,
        )

    print(
        "Cycle complete:",
        checkpoint.get("cycle_complete"),
    )

    print()


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

    for label, key in fields:
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
        print("Items recorded for review/retry:")

        for error in errors:
            print(error)


def run_retry_pass(
    sync: MobileSentrixWorkbookSyncService,
) -> dict[str, object]:
    print()
    print("Running retry pass...")

    try:
        result = sync.retry_failed_items(
            max_items=RETRY_MAX_ITEMS,
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
            event="retry_pass_exception",
            extra={
                "exception_type": (type(exc).__name__),
                "exception": str(exc),
            },
        )

        raise

    print(
        "Retry items processed:",
        result.get("retry_items_processed"),
    )

    print(
        "Recovered:",
        result.get("recovered"),
    )

    print(
        "Still pending:",
        result.get("still_pending"),
    )

    print(
        "Unmatched:",
        result.get("unmatched"),
    )

    print(
        "Exhausted:",
        result.get("exhausted"),
    )

    print(
        "Retry API errors:",
        result.get("api_errors"),
    )

    print(
        "Retry count remaining:",
        result.get("retry_count"),
    )

    return result


def run() -> int:
    print_header()

    print("Initializing synchronization service...")

    sync = MobileSentrixWorkbookSyncService()

    print("Synchronization service initialized.")

    print()

    print_checkpoint(sync)

    checkpoint = sync.get_sync_checkpoint()

    (
        pending_count,
        unmatched_count,
        exhausted_count,
        other_count,
    ) = get_retry_status_counts(checkpoint)

    next_start_row = checkpoint.get("next_start_row")

    cycle_complete = bool(
        checkpoint.get(
            "cycle_complete",
            False,
        )
    )

    # ========================================================
    # Completed-cycle handling
    # ========================================================

    if cycle_complete and next_start_row is None and pending_count == 0:
        print("Synchronization cycle is already complete.")

        if unmatched_count > 0:
            print(
                "Unmatched/manual-review items " "remain recorded:",
                unmatched_count,
            )

        if exhausted_count > 0:
            print(
                "Exhausted/manual-review items " "remain recorded:",
                exhausted_count,
            )

        if other_count > 0:
            print(
                "Other retry-state items " "remain recorded:",
                other_count,
            )

        write_state_snapshot(
            sync=sync,
            event="already_complete",
            extra={
                "pending_retries": (pending_count),
                "unmatched_retries": (unmatched_count),
                "exhausted_retries": (exhausted_count),
                "other_retry_states": (other_count),
            },
        )

        return 0

    # ========================================================
    # Initial Dedicated IP verification
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
        event="runner_started",
        extra={
            "public_ip": public_ip,
        },
    )

    checkpoint = sync.get_sync_checkpoint()

    (
        pending_count,
        unmatched_count,
        exhausted_count,
        other_count,
    ) = get_retry_status_counts(checkpoint)

    next_start_row = checkpoint.get("next_start_row")

    # ========================================================
    # Primary scan already finished
    # ========================================================

    if next_start_row is None:
        if pending_count > 0:
            print()
            print("Primary scan is complete.")

            print(
                "Pending retry items remain:",
                pending_count,
            )

            retry_result = run_retry_pass(sync)

            checkpoint = sync.get_sync_checkpoint()

            (
                pending_count,
                unmatched_count,
                exhausted_count,
                other_count,
            ) = get_retry_status_counts(checkpoint)

            if pending_count == 0:
                print()
                print("No pending retries remain.")

                if unmatched_count > 0:
                    print(
                        "Unmatched/manual-review " "items remain recorded:",
                        unmatched_count,
                    )

                if exhausted_count > 0:
                    print(
                        "Exhausted/manual-review " "items remain recorded:",
                        exhausted_count,
                    )

                if other_count > 0:
                    print(
                        "Other retry-state items " "remain recorded:",
                        other_count,
                    )

                print("Primary synchronization " "work is complete.")

                write_state_snapshot(
                    sync=sync,
                    event=("primary_complete_" "no_pending_retries"),
                    extra={
                        "pending_retries": (pending_count),
                        "unmatched_retries": (unmatched_count),
                        "exhausted_retries": (exhausted_count),
                        "other_retry_states": (other_count),
                        "retry_api_errors": (retry_result.get("api_errors")),
                    },
                )

            else:
                print()
                print("Retry items remain pending.")

                print(
                    "Stopping this runner so " "they are not retried " "continuously."
                )

                write_state_snapshot(
                    sync=sync,
                    event=("primary_complete_" "pending_retries"),
                    extra={
                        "pending_retries": (pending_count),
                        "unmatched_retries": (unmatched_count),
                        "exhausted_retries": (exhausted_count),
                        "other_retry_states": (other_count),
                    },
                )

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
                0,
            )

            print()

            print_checkpoint(sync)

            write_state_snapshot(
                sync=sync,
                event="runner_stopped_normally",
                extra={
                    "batches_completed": 0,
                },
            )

            return 0

        print()
        print("Primary scan is complete.")

        print("No pending retries remain.")

        if unmatched_count > 0:
            print(
                "Unmatched/manual-review " "items remain recorded:",
                unmatched_count,
            )

        if exhausted_count > 0:
            print(
                "Exhausted/manual-review " "items remain recorded:",
                exhausted_count,
            )

        if other_count > 0:
            print(
                "Other retry-state items " "remain recorded:",
                other_count,
            )

        print("Primary synchronization " "work is complete.")

        write_state_snapshot(
            sync=sync,
            event=("primary_complete_" "no_pending_retries"),
            extra={
                "pending_retries": (pending_count),
                "unmatched_retries": (unmatched_count),
                "exhausted_retries": (exhausted_count),
                "other_retry_states": (other_count),
            },
        )

        return 0

    batches_completed = 0

    while batches_completed < MAX_BATCHES_PER_RUN:
        checkpoint = sync.get_sync_checkpoint()

        next_start_row = checkpoint.get("next_start_row")

        (
            pending_count,
            unmatched_count,
            exhausted_count,
            other_count,
        ) = get_retry_status_counts(checkpoint)

        # ==================================================
        # Primary scan finished
        # ==================================================

        if next_start_row is None:
            if pending_count > 0:
                retry_result = run_retry_pass(sync)

                checkpoint = sync.get_sync_checkpoint()

                (
                    pending_count,
                    unmatched_count,
                    exhausted_count,
                    other_count,
                ) = get_retry_status_counts(checkpoint)

                if pending_count == 0:
                    print()
                    print("No pending retries remain.")

                    if unmatched_count > 0:
                        print(
                            "Unmatched/manual-review " "items remain recorded:",
                            unmatched_count,
                        )

                    if exhausted_count > 0:
                        print(
                            "Exhausted/manual-review " "items remain recorded:",
                            exhausted_count,
                        )

                    if other_count > 0:
                        print(
                            "Other retry-state items " "remain recorded:",
                            other_count,
                        )

                    print("Primary synchronization " "work is complete.")

                    write_state_snapshot(
                        sync=sync,
                        event=("primary_complete_" "no_pending_retries"),
                        extra={
                            "pending_retries": (pending_count),
                            "unmatched_retries": (unmatched_count),
                            "exhausted_retries": (exhausted_count),
                            "other_retry_states": (other_count),
                            "retry_api_errors": (retry_result.get("api_errors")),
                        },
                    )

                    break

                print()
                print("Retry items remain pending.")

                print(
                    "Stopping this runner so " "they are not retried " "continuously."
                )

                write_state_snapshot(
                    sync=sync,
                    event=("primary_complete_" "pending_retries"),
                    extra={
                        "pending_retries": (pending_count),
                        "unmatched_retries": (unmatched_count),
                        "exhausted_retries": (exhausted_count),
                        "other_retry_states": (other_count),
                    },
                )

                break

            print()
            print("Primary scan is complete.")

            print("No pending retries remain.")

            if unmatched_count > 0:
                print(
                    "Unmatched/manual-review " "items remain recorded:",
                    unmatched_count,
                )

            if exhausted_count > 0:
                print(
                    "Exhausted/manual-review " "items remain recorded:",
                    exhausted_count,
                )

            if other_count > 0:
                print(
                    "Other retry-state items " "remain recorded:",
                    other_count,
                )

            print("Primary synchronization " "work is complete.")

            write_state_snapshot(
                sync=sync,
                event=("primary_complete_" "no_pending_retries"),
                extra={
                    "pending_retries": (pending_count),
                    "unmatched_retries": (unmatched_count),
                    "exhausted_retries": (exhausted_count),
                    "other_retry_states": (other_count),
                },
            )

            break

        batch_number = batches_completed + 1

        # ==================================================
        # Verify VPN / Dedicated IP before every batch
        # ==================================================

        ip_ok, public_ip = verify_public_ip(
            batch_number=batch_number,
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
                batch_number=batch_number,
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
            f"Starting batch {batch_number} "
            f"from workbook row "
            f"{next_start_row}..."
        )

        print(
            "Public IP:",
            public_ip,
        )

        write_state_snapshot(
            sync=sync,
            event="batch_starting",
            batch_number=batch_number,
            extra={
                "start_row": (next_start_row),
                "public_ip": (public_ip),
            },
        )

        try:
            result = sync.sync_next_batch(
                batch_size=BATCH_SIZE,
                request_delay_seconds=(REQUEST_DELAY_SECONDS),
            )

        except KeyboardInterrupt:
            print()
            print()
            print("RUN INTERRUPTED BY USER")

            print("KeyboardInterrupt received.")

            write_state_snapshot(
                sync=sync,
                event="keyboard_interrupt",
                batch_number=batch_number,
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
                event="batch_exception",
                batch_number=batch_number,
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
            batch_number=batch_number,
            result=result,
        )

        checkpoint = sync.get_sync_checkpoint()

        (
            pending_count,
            unmatched_count,
            exhausted_count,
            other_count,
        ) = get_retry_status_counts(checkpoint)

        write_state_snapshot(
            sync=sync,
            event="batch_completed",
            batch_number=batch_number,
            extra={
                "public_ip": (public_ip),
                "products_processed": (result.get("products_processed")),
                "exact_matches": (result.get("exact_matches")),
                "api_errors": (result.get("api_errors")),
                "retry_count": (get_retry_count(checkpoint)),
                "pending_retries": (pending_count),
                "unmatched_retries": (unmatched_count),
                "exhausted_retries": (exhausted_count),
                "other_retry_states": (other_count),
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
                batch_number=batch_number,
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
                event=("zero_products_safety_stop"),
                batch_number=batch_number,
            )

            break

        # ==================================================
        # Retry queue status
        # ==================================================

        print()
        print("Retry queue status:")

        print(
            "  Pending:",
            pending_count,
        )

        print(
            "  Unmatched:",
            unmatched_count,
        )

        print(
            "  Exhausted:",
            exhausted_count,
        )

        if other_count:
            print(
                "  Other:",
                other_count,
            )

        print(
            "Retained unmatched/manual-review " "records do not stop the primary scan."
        )

        # ==================================================
        # Periodic retry processing
        # ==================================================

        if batches_completed % RETRY_EVERY_BATCHES == 0:
            checkpoint = sync.get_sync_checkpoint()

            (
                pending_count,
                unmatched_count,
                exhausted_count,
                other_count,
            ) = get_retry_status_counts(checkpoint)

            if pending_count > 0:
                retry_result = run_retry_pass(sync)

                retry_api_errors = get_int(retry_result.get("api_errors"))

                write_state_snapshot(
                    sync=sync,
                    event=("retry_pass_completed"),
                    batch_number=batch_number,
                    extra={
                        "retry_items_processed": (
                            retry_result.get("retry_items_processed")
                        ),
                        "recovered": (retry_result.get("recovered")),
                        "still_pending": (retry_result.get("still_pending")),
                        "unmatched": (retry_result.get("unmatched")),
                        "exhausted": (retry_result.get("exhausted")),
                        "api_errors": (retry_api_errors),
                        "retry_count": (retry_result.get("retry_count")),
                    },
                )

                if retry_api_errors >= MAX_BATCH_API_ERRORS:
                    print()
                    print("STOPPING:")

                    print(
                        "The retry pass reached " "the API error safety " "threshold."
                    )

                    write_state_snapshot(
                        sync=sync,
                        event=("retry_api_error_" "safety_stop"),
                        batch_number=batch_number,
                        extra={
                            "retry_api_errors": (retry_api_errors),
                        },
                    )

                    break

            else:
                print()
                print("Periodic retry pass skipped:")

                print("No pending retry items remain.")

        # ==================================================
        # Check whether primary scan finished
        # ==================================================

        checkpoint = sync.get_sync_checkpoint()

        next_start_row = checkpoint.get("next_start_row")

        (
            pending_count,
            unmatched_count,
            exhausted_count,
            other_count,
        ) = get_retry_status_counts(checkpoint)

        if next_start_row is None and pending_count == 0:
            print()
            print("Primary scan is complete.")

            if unmatched_count > 0:
                print(
                    "Unmatched items remain " "for manual review:",
                    unmatched_count,
                )

            if exhausted_count > 0:
                print(
                    "Exhausted retry items " "remain for manual review:",
                    exhausted_count,
                )

            if other_count > 0:
                print(
                    "Nonstandard retry records " "remain for manual review:",
                    other_count,
                )

            if unmatched_count == 0 and exhausted_count == 0 and other_count == 0:
                print("No retry work remains.")

            write_state_snapshot(
                sync=sync,
                event=("primary_scan_complete"),
                batch_number=batch_number,
                extra={
                    "pending_retries": (pending_count),
                    "unmatched_retries": (unmatched_count),
                    "exhausted_retries": (exhausted_count),
                    "other_retry_states": (other_count),
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

    print_checkpoint(sync)

    write_state_snapshot(
        sync=sync,
        event="runner_stopped_normally",
        extra={
            "batches_completed": (batches_completed),
        },
    )

    return 0


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
