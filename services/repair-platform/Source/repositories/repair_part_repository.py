"""
============================================================
Nocturnix Repair Platform
Repair Part Repository
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Status:
    Placeholder

Purpose:
    Repository responsible for tracking parts used
    on repair tickets.

Planned Features:
    • Parts assigned to repair tickets
    • Part quantities
    • Installed serial numbers
    • Cost tracking
    • Warranty tracking

============================================================
"""

from repositories.repository_base import RepositoryBase


class RepairPartRepository(RepositoryBase):
    """
    Placeholder repository for repair parts.
    """

    def __init__(self, database):

        super().__init__(database, "repair_parts")
