"""
============================================================
Nocturnix Business Portal
Technical Knowledge Service
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Purpose:
    Business logic for the Technical Knowledge System.

============================================================
"""

from repositories.guide_repository import GuideRepository


class TechnicalKnowledgeService:

    def __init__(self, repositories):

        self.repositories = repositories

        self.guides: GuideRepository = repositories.guides

    # ======================================================
    # Collections
    # ======================================================

    def all(self):

        return self.guides.all_guides()

    # ======================================================
    # Standard Interface
    # ======================================================


    def search(self, text=""):

        return self.search_guides(text)


    def count(self):

        return len(self.guides.all_guides())


    def exists(self, guide_id):

        return self.guide_exists(guide_id)

    # ======================================================
    # Search
    # ======================================================

    def search_guides(self, text=""):

        return self.guides.search(text)

    # ======================================================
    # Filters
    # ======================================================

    def guides_by_device(self, device_id):

        return self.guides.by_device(device_id)

    def guides_by_service(self, service_id):

        return self.guides.by_service(service_id)

    def guides_by_category(self, category_id):

        return self.guides.by_category(category_id)

    def guides_by_source(self, source_id):

        return self.guides.by_source(source_id)

    # ======================================================
    # Single Record
    # ======================================================

    def get_guide(self, guide_id):

        return self.guides.get(guide_id)

    def guide_exists(self, guide_id):

        return self.guides.exists("Guide ID", guide_id)
