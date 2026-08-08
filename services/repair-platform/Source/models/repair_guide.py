"""
============================================================
Nocturnix Business Portal
Repair Guide Model
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Purpose:
    Represents a repair guide contained within the
    Nocturnix Master Database.

Table:
    tblRepairGuides

============================================================
"""

from dataclasses import dataclass

from core.base_model import BaseModel


@dataclass
class RepairGuide(BaseModel):
    """
    Business model representing a repair guide.
    """

    guide_id: str = ""

    device_id: str = ""

    device_name: str = ""

    manufacturer: str = ""

    device_family: str = ""

    service_id: str = ""

    service_name: str = ""

    category_id: str = ""

    category_name: str = ""

    source_id: str = ""

    source_name: str = ""

    title: str = ""

    guide_url: str = ""

    embed_url: str = ""

    difficulty: str = ""

    estimated_minutes: int = 0

    version: str = ""

    active: bool = True

    notes: str = ""

    def display_name(self) -> str:
        """
        Returns a user-friendly display name.
        """

        return f"{self.device_name} - " f"{self.service_name}"
