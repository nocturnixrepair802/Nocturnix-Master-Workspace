"""
============================================================
Nocturnix Repair Platform
Guide Source Repository
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Status:
    Placeholder

Purpose:
    Repository responsible for managing repair guide
    sources and references.

Planned Features:
    • OEM manuals
    • Internal procedures
    • External references
    • Source management

============================================================
"""

from repositories.repository_base import RepositoryBase


class GuideSourceRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "guide_sources")
