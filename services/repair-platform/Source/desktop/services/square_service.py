from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

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

    def list_locations(self) -> list[SquareLocation]:
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

    def verify_connection(self) -> SquareLocation:
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

    # ---------------------------------------------------------
    # SANDBOX PAYMENT
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

        card_details = payment.card_details

        source_type = ""

        if card_details is not None:
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
