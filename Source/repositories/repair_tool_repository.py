"""
============================================================
Nocturnix Repair Platform
Repair Tool Repository
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Status:
    Placeholder

Purpose:
    Repository responsible for tools required to perform
    specific repairs.

Planned Features:
    • Required tools
    • Optional tools
    • Tool compatibility
    • Tool inventory

============================================================
"""

from repositories.repository_base import RepositoryBase


class RepairToolRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "repair_tools")
