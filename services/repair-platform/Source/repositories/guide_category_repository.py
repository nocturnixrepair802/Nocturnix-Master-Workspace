"""
============================================================
Nocturnix Repair Platform
Guide Category Repository
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Status:
    Placeholder

Purpose:
    Repository responsible for repair guide categories.

Planned Features:
    • Guide categories
    • Category hierarchy
    • Category lookup

============================================================
"""

from repositories.repository_base import RepositoryBase


class GuideCategoryRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "guide_categories")
