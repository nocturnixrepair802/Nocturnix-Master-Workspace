"""
============================================================
Nocturnix Repair Platform
Tool Repository
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Status:
    Placeholder

Purpose:
    Repository responsible for the master tool catalog.

Planned Features:
    • Tool inventory
    • Tool categories
    • Manufacturer
    • Storage location
    • Calibration records
    • Purchase information

============================================================
"""

from repositories.repository_base import RepositoryBase


class ToolRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "tool_catalog")
