"""
============================================================
Nocturnix Business Portal
Guide Repository
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Purpose:
    Repository responsible for Repair Guide records.

Table:
    repair_guides

============================================================
"""

from repositories.repository_base import RepositoryBase


class GuideRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "repair_guides")

    # ======================================================
    # Collections
    # ======================================================

    def all(self):

        return super().all()

    # ======================================================
    # Search
    # ======================================================

    def search(self, text=""):

        if not text:
            return self.table.copy()

        text = str(text).lower()

        mask = (
            self.table["Device Name"].fillna("").str.lower().str.contains(text)
            | self.table["Service Name"].fillna("").str.lower().str.contains(text)
            | self.table["Guide Title"].fillna("").str.lower().str.contains(text)
        )

        return self.table.loc[mask].copy()

    # ======================================================
    # Filters
    # ======================================================

    def by_device(self, device_id):

        return self.filter("Device ID", device_id)

    def by_service(self, service_id):

        return self.filter("Service ID", service_id)

    def by_category(self, category_id):

        return self.filter("Category ID", category_id)

    def by_source(self, source_id):

        return self.filter("Source ID", source_id)

    # ======================================================
    # Single Record
    # ======================================================

    def get(self, guide_id):

        return self.first("Guide ID", guide_id)
