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
from typing import Optional

import pandas as pd


@dataclass
class RepairSession:

    # ======================================================
    # Customer
    # ======================================================

    customer: Optional[pd.Series] = None

    customer_device: Optional[pd.Series] = None

    # ======================================================
    # Device
    # ======================================================

    device: Optional[pd.Series] = None

    # ======================================================
    # Repair
    # ======================================================

    service: Optional[pd.Series] = None

    compatibility: Optional[pd.Series] = None

    repair_guide: Optional[pd.Series] = None

    # ======================================================
    # Pricing
    # ======================================================

    labor: Optional[pd.Series] = None

    pricing: Optional[pd.Series] = None

    parts: list = field(default_factory=list)

    # ======================================================
    # Ticket
    # ======================================================

    repair_ticket: Optional[pd.Series] = None

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
