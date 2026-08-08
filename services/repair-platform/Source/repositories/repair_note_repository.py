"""
============================================================
Nocturnix Repair Platform
Repair Note Repository
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Status:
    Placeholder

Purpose:
    Repository responsible for technician notes and repair
    history attached to repair tickets.

Planned Features:
    • Technician notes
    • Customer communication
    • Timeline history
    • Internal notes

============================================================
"""

from repositories.repository_base import RepositoryBase


class RepairNoteRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "repair_notes")
