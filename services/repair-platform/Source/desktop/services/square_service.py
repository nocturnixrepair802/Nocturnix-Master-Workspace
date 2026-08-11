from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from square import Square
from square.environment import SquareEnvironment

PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class SquareLocation:
    location_id: str
    name: str
    status: str
    currency: str
    country: str


@dataclass(frozen=True)
class SquarePayment:
    payment_id: str
    order_id: str
    status: str
    amount: float
    currency: str
    receipt_url: str
    source_type: str


@dataclass(frozen=True)
class SquareRefund:
    refund_id: str
    payment_id: str
    status: str
    amount: float
    currency: str
    reason: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SquareTerminalCheckout:
    checkout_id: str
    status: str
    amount: float
    currency: str
    device_id: str
    payment_ids: list[str]
    reference_id: str
    created_at: str
    updated_at: str
    cancel_reason: str


class SquareService:
    SANDBOX_CARD_SOURCE_ID = "cnon:card-nonce-ok"

    def __init__(self) -> None:
        self.access_token = os.getenv(
            "SQUARE_ACCESS_TOKEN",
            "",
        ).strip()

        self.location_id = os.getenv(
            "SQUARE_LOCATION_ID",
            "",
        ).strip()

        self.application_id = os.getenv(
            "SQUARE_APPLICATION_ID",
            "",
        ).strip()

        self.terminal_device_id = os.getenv(
            "SQUARE_TERMINAL_DEVICE_ID",
            "",
        ).strip()

        if not self.access_token:
            raise RuntimeError("SQUARE_ACCESS_TOKEN is not configured.")

        if not self.location_id:
            raise RuntimeError("SQUARE_LOCATION_ID is not configured.")

        self.client = Square(
            token=self.access_token,
            environment=SquareEnvironment.SANDBOX,
        )

    # ---------------------------------------------------------
    # LOCATION
    # ---------------------------------------------------------

    def list_locations(
        self,
    ) -> list[SquareLocation]:
        response = self.client.locations.list()

        locations: list[SquareLocation] = []

        for location in response.locations or []:
            locations.append(
                SquareLocation(
                    location_id=str(location.id or ""),
                    name=str(location.name or ""),
                    status=str(location.status or ""),
                    currency=str(location.currency or ""),
                    country=str(location.country or ""),
                )
            )

        return locations

    def verify_connection(
        self,
    ) -> SquareLocation:
        locations = self.list_locations()

        if not locations:
            raise RuntimeError(
                "Square Sandbox connection succeeded, "
                "but no locations were returned."
            )

        for location in locations:
            if location.location_id == self.location_id:
                return location

        raise RuntimeError(
            "Square connection succeeded, but "
            "SQUARE_LOCATION_ID did not match "
            "any Sandbox location."
        )

    # ---------------------------------------------------------
    # MONEY
    # ---------------------------------------------------------

    @staticmethod
    def _amount_to_cents(
        amount: float,
    ) -> int:
        decimal_amount = Decimal(str(amount)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        cents = int(decimal_amount * 100)

        if cents <= 0:
            raise ValueError("Square payment amount must be " "greater than zero.")

        return cents

    @staticmethod
    def _money_to_float(
        money: object,
    ) -> float:
        if money is None:
            return 0.0

        amount = getattr(
            money,
            "amount",
            0,
        )

        try:
            cents = int(amount or 0)
        except (TypeError, ValueError):
            return 0.0

        return round(
            cents / 100,
            2,
        )

    @staticmethod
    def _money_currency(
        money: object,
    ) -> str:
        if money is None:
            return "USD"

        currency = getattr(
            money,
            "currency",
            None,
        )

        if currency is None:
            return "USD"

        return str(currency)

    # ---------------------------------------------------------
    # SANDBOX DIRECT PAYMENT
    # ---------------------------------------------------------

    def create_sandbox_card_payment(
        self,
        *,
        amount: float,
        repair_id: str,
        note: str = "",
    ) -> SquarePayment:
        cents = self._amount_to_cents(amount)

        idempotency_key = str(uuid.uuid4())

        payment_note = note.strip() or f"Nocturnix repair {repair_id}"

        response = self.client.payments.create(
            source_id=self.SANDBOX_CARD_SOURCE_ID,
            idempotency_key=idempotency_key,
            amount_money={
                "amount": cents,
                "currency": "USD",
            },
            location_id=self.location_id,
            note=payment_note,
            reference_id=repair_id,
            autocomplete=True,
        )

        payment = response.payment

        if payment is None:
            raise RuntimeError("Square did not return a payment.")

        amount_money = payment.amount_money

        returned_cents = 0

        if amount_money is not None:
            returned_cents = int(amount_money.amount or 0)

        returned_currency = "USD"

        if amount_money is not None and amount_money.currency is not None:
            returned_currency = str(amount_money.currency)

        source_type = ""

        if payment.card_details is not None:
            source_type = "Card"

        return SquarePayment(
            payment_id=str(payment.id or ""),
            order_id=str(payment.order_id or ""),
            status=str(payment.status or ""),
            amount=round(
                returned_cents / 100,
                2,
            ),
            currency=returned_currency,
            receipt_url=str(payment.receipt_url or ""),
            source_type=source_type,
        )

    # ---------------------------------------------------------
    # TERMINAL CONFIGURATION
    # ---------------------------------------------------------

    def require_terminal_device_id(
        self,
    ) -> str:
        if not self.terminal_device_id:
            raise RuntimeError("SQUARE_TERMINAL_DEVICE_ID is not configured.")

        return self.terminal_device_id

    # ---------------------------------------------------------
    # TERMINAL CHECKOUT
    # ---------------------------------------------------------

    def create_terminal_checkout(
        self,
        *,
        amount: float,
        repair_id: str,
        note: str = "",
        device_id: str = "",
    ) -> SquareTerminalCheckout:
        cents = self._amount_to_cents(amount)

        selected_device_id = device_id.strip() or self.require_terminal_device_id()

        checkout_note = note.strip() or f"Nocturnix repair {repair_id}"

        idempotency_key = str(uuid.uuid4())

        response = self.client.terminal.checkouts.create(
            idempotency_key=idempotency_key,
            checkout={
                "amount_money": {
                    "amount": cents,
                    "currency": "USD",
                },
                "device_options": {
                    "device_id": selected_device_id,
                },
                "reference_id": repair_id,
                "note": checkout_note,
            },
        )

        checkout = response.checkout

        if checkout is None:
            raise RuntimeError("Square did not return a Terminal checkout.")

        return self._terminal_checkout_from_square(checkout)

    def get_terminal_checkout(
        self,
        checkout_id: str,
    ) -> SquareTerminalCheckout:
        checkout_id = str(checkout_id).strip()

        if not checkout_id:
            raise ValueError("Terminal checkout ID is required.")

        response = self.client.terminal.checkouts.get(checkout_id=checkout_id)

        checkout = response.checkout

        if checkout is None:
            raise RuntimeError(
                "Square did not return the requested " "Terminal checkout."
            )

        return self._terminal_checkout_from_square(checkout)

    def cancel_terminal_checkout(
        self,
        checkout_id: str,
    ) -> SquareTerminalCheckout:
        checkout_id = str(checkout_id).strip()

        if not checkout_id:
            raise ValueError("Terminal checkout ID is required.")

        response = self.client.terminal.checkouts.cancel(checkout_id=checkout_id)

        checkout = response.checkout

        if checkout is None:
            raise RuntimeError(
                "Square did not return the cancelled " "Terminal checkout."
            )

        return self._terminal_checkout_from_square(checkout)

    # ---------------------------------------------------------
    # TERMINAL RESULT HELPERS
    # ---------------------------------------------------------

    def _terminal_checkout_from_square(
        self,
        checkout: Any,
    ) -> SquareTerminalCheckout:
        amount_money = getattr(
            checkout,
            "amount_money",
            None,
        )

        device_options = getattr(
            checkout,
            "device_options",
            None,
        )

        device_id = ""

        if device_options is not None:
            device_id = str(
                getattr(
                    device_options,
                    "device_id",
                    "",
                )
                or ""
            )

        payment_ids_raw = getattr(
            checkout,
            "payment_ids",
            None,
        )

        payment_ids: list[str] = []

        if payment_ids_raw:
            payment_ids = [
                str(payment_id) for payment_id in payment_ids_raw if payment_id
            ]

        cancel_reason = str(
            getattr(
                checkout,
                "cancel_reason",
                "",
            )
            or ""
        )

        return SquareTerminalCheckout(
            checkout_id=str(
                getattr(
                    checkout,
                    "id",
                    "",
                )
                or ""
            ),
            status=str(
                getattr(
                    checkout,
                    "status",
                    "",
                )
                or ""
            ),
            amount=self._money_to_float(amount_money),
            currency=self._money_currency(amount_money),
            device_id=device_id,
            payment_ids=payment_ids,
            reference_id=str(
                getattr(
                    checkout,
                    "reference_id",
                    "",
                )
                or ""
            ),
            created_at=str(
                getattr(
                    checkout,
                    "created_at",
                    "",
                )
                or ""
            ),
            updated_at=str(
                getattr(
                    checkout,
                    "updated_at",
                    "",
                )
                or ""
            ),
            cancel_reason=cancel_reason,
        )

    # ---------------------------------------------------------
    # PAYMENT LOOKUP
    # ---------------------------------------------------------

    def get_payment(
        self,
        payment_id: str,
    ) -> SquarePayment:
        payment_id = str(payment_id).strip()

        if not payment_id:
            raise ValueError("Square payment ID is required.")

        response = self.client.payments.get(payment_id=payment_id)

        payment = response.payment

        if payment is None:
            raise RuntimeError("Square did not return the requested payment.")

        amount_money = payment.amount_money

        return SquarePayment(
            payment_id=str(payment.id or ""),
            order_id=str(payment.order_id or ""),
            status=str(payment.status or ""),
            amount=self._money_to_float(amount_money),
            currency=self._money_currency(amount_money),
            receipt_url=str(payment.receipt_url or ""),
            source_type=("Card" if payment.card_details is not None else ""),
        )
    # ---------------------------------------------------------
    # REFUNDS
    # ---------------------------------------------------------

    def refund_payment(
        self,
        *,
        payment_id: str,
        amount: float,
        reason: str = "",
    ) -> SquareRefund:
        payment_id = str(payment_id).strip()

        if not payment_id:
            raise ValueError("Square payment ID is required.")

        cents = self._amount_to_cents(amount)

        refund_reason = reason.strip() or "Nocturnix repair payment refund"

        response = self.client.refunds.refund_payment(
            idempotency_key=str(uuid.uuid4()),
            amount_money={
                "amount": cents,
                "currency": "USD",
            },
            payment_id=payment_id,
            reason=refund_reason,
        )

        refund = response.refund

        if refund is None:
            raise RuntimeError("Square did not return a refund.")

        amount_money = refund.amount_money

        return SquareRefund(
            refund_id=str(refund.id or ""),
            payment_id=str(refund.payment_id or ""),
            status=str(refund.status or ""),
            amount=self._money_to_float(amount_money),
            currency=self._money_currency(amount_money),
            reason=str(refund.reason or ""),
            created_at=str(refund.created_at or ""),
            updated_at=str(refund.updated_at or ""),
        )

    def get_refund(
        self,
        refund_id: str,
    ) -> SquareRefund:
        refund_id = str(refund_id).strip()

        if not refund_id:
            raise ValueError("Square refund ID is required.")

        response = self.client.refunds.get(refund_id=refund_id)

        refund = response.refund

        if refund is None:
            raise RuntimeError("Square did not return the requested refund.")

        amount_money = refund.amount_money

        return SquareRefund(
            refund_id=str(refund.id or ""),
            payment_id=str(refund.payment_id or ""),
            status=str(refund.status or ""),
            amount=self._money_to_float(amount_money),
            currency=self._money_currency(amount_money),
            reason=str(refund.reason or ""),
            created_at=str(refund.created_at or ""),
            updated_at=str(refund.updated_at or ""),
        )
