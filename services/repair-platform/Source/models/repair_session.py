"""
============================================================
Nocturnix Repair Platform
Repair Session
============================================================

Purpose:
    Holds the complete state of a repair while it is
    being created by the Repair Wizard.

============================================================
"""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class RepairSession:

    # ======================================================
    # Customer
    # ======================================================

    customer: pd.Series | None = None

    customer_device: pd.Series | None = None

    # ======================================================
    # Device
    # ======================================================

    device: pd.Series | None = None

    # ======================================================
    # Repair
    # ======================================================

    service: pd.Series | None = None

    compatibility: pd.Series | None = None

    repair_guide: pd.Series | None = None

    # ======================================================
    # Pricing
    # ======================================================

    labor: pd.Series | None = None

    pricing: pd.Series | None = None

    parts: list = field(default_factory=list)

    # ======================================================
    # Ticket
    # ======================================================

    repair_ticket: pd.Series | None = None

    # ======================================================
    # Utility
    # ======================================================

    def reset(self):

        self.customer = None
        self.customer_device = None
        self.device = None
        self.service = None
        self.compatibility = None
        self.repair_guide = None
        self.labor = None
        self.pricing = None
        self.parts = []
        self.repair_ticket = None

    @property
    def is_complete(self):

        return all(
            [
                self.customer is not None,
                self.device is not None,
                self.service is not None,
            ]
        )
