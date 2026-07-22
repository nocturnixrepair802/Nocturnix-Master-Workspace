"""
============================================================
Nocturnix Repair Platform
Technical Document Repository
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Status:
    Placeholder

Purpose:
    Repository responsible for technical documentation.

Planned Features:
    • Service manuals
    • Schematics
    • Board views
    • PDF documentation

============================================================
"""

from repositories.repository_base import RepositoryBase


class TechnicalDocumentRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "technical_documents")
